import AVFoundation
import Foundation

enum MergeError: Error, CustomStringConvertible {
    case usage(String)
    case missingTrack(String)
    case exportFailed(String)

    var description: String {
        switch self {
        case .usage(let message):
            return message
        case .missingTrack(let message):
            return message
        case .exportFailed(let message):
            return message
        }
    }
}

struct Arguments {
    let videoURL: URL
    let audioURL: URL
    let outputURL: URL
    let replace: Bool
}

func parseArguments() throws -> Arguments {
    var videoPath: String?
    var audioPath: String?
    var outputPath: String?
    var replace = false

    var iterator = CommandLine.arguments.dropFirst().makeIterator()
    while let arg = iterator.next() {
        switch arg {
        case "--video":
            videoPath = iterator.next()
        case "--audio":
            audioPath = iterator.next()
        case "--output":
            outputPath = iterator.next()
        case "--replace":
            replace = true
        default:
            throw MergeError.usage("Unknown argument: \(arg)")
        }
    }

    guard let videoPath, let audioPath, let outputPath else {
        throw MergeError.usage("Usage: swift merge_audio_into_video.swift --video <video.mp4> --audio <audio.mp3> --output <out.mp4> [--replace]")
    }

    return Arguments(
        videoURL: URL(fileURLWithPath: videoPath),
        audioURL: URL(fileURLWithPath: audioPath),
        outputURL: URL(fileURLWithPath: outputPath),
        replace: replace
    )
}

func merge(videoURL: URL, audioURL: URL, outputURL: URL, replace: Bool) throws {
    let fileManager = FileManager.default
    if replace, fileManager.fileExists(atPath: outputURL.path) {
        try fileManager.removeItem(at: outputURL)
    }

    let videoAsset = AVURLAsset(url: videoURL)
    let audioAsset = AVURLAsset(url: audioURL)

    guard let sourceVideoTrack = videoAsset.tracks(withMediaType: .video).first else {
        throw MergeError.missingTrack("Missing video track: \(videoURL.path)")
    }
    guard let sourceAudioTrack = audioAsset.tracks(withMediaType: .audio).first else {
        throw MergeError.missingTrack("Missing audio track: \(audioURL.path)")
    }

    let composition = AVMutableComposition()
    guard let compositionVideoTrack = composition.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid) else {
        throw MergeError.missingTrack("Unable to create composition video track")
    }
    guard let compositionAudioTrack = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid) else {
        throw MergeError.missingTrack("Unable to create composition audio track")
    }

    let audioDuration = audioAsset.duration
    let videoDuration = videoAsset.duration
    let targetDuration = audioDuration
    let frameRate = sourceVideoTrack.nominalFrameRate > 0 ? sourceVideoTrack.nominalFrameRate : 30
    let frameDuration = CMTime(value: 1, timescale: CMTimeScale(frameRate.rounded()))
    let freezeFrameDuration = CMTimeMaximum(frameDuration, CMTime(value: 1, timescale: 600))

    let baseVideoDuration = CMTimeMinimum(videoDuration, targetDuration)
    try compositionVideoTrack.insertTimeRange(
        CMTimeRange(start: .zero, duration: baseVideoDuration),
        of: sourceVideoTrack,
        at: .zero
    )

    if targetDuration > videoDuration {
        let lastFrameStart = CMTimeSubtract(videoDuration, freezeFrameDuration)
        let safeLastFrameStart = lastFrameStart >= .zero ? lastFrameStart : .zero
        let extensionDuration = CMTimeSubtract(targetDuration, videoDuration)
        let extensionSegments = Int(ceil(CMTimeGetSeconds(extensionDuration) / CMTimeGetSeconds(freezeFrameDuration)))

        var insertAt = videoDuration
        for _ in 0..<extensionSegments {
            let remainingDuration = CMTimeSubtract(targetDuration, insertAt)
            if remainingDuration <= .zero {
                break
            }
            let nextSegmentDuration = CMTimeMinimum(freezeFrameDuration, remainingDuration)
            try compositionVideoTrack.insertTimeRange(
                CMTimeRange(start: safeLastFrameStart, duration: nextSegmentDuration),
                of: sourceVideoTrack,
                at: insertAt
            )
            insertAt = CMTimeAdd(insertAt, nextSegmentDuration)
        }
    }
    compositionVideoTrack.preferredTransform = sourceVideoTrack.preferredTransform

    try compositionAudioTrack.insertTimeRange(
        CMTimeRange(start: .zero, duration: audioDuration),
        of: sourceAudioTrack,
        at: .zero
    )

    guard let exportSession = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetHighestQuality) else {
        throw MergeError.exportFailed("Unable to create AVAssetExportSession")
    }

    outputURL.deletingLastPathComponent().withUnsafeFileSystemRepresentation { _ in
        try? fileManager.createDirectory(at: outputURL.deletingLastPathComponent(), withIntermediateDirectories: true)
    }

    exportSession.outputURL = outputURL
    exportSession.outputFileType = .mp4
    exportSession.shouldOptimizeForNetworkUse = true

    let semaphore = DispatchSemaphore(value: 0)
    exportSession.exportAsynchronously {
        semaphore.signal()
    }
    semaphore.wait()

    switch exportSession.status {
    case .completed:
        return
    case .failed:
        throw MergeError.exportFailed(exportSession.error?.localizedDescription ?? "Unknown export failure")
    case .cancelled:
        throw MergeError.exportFailed("Export cancelled")
    default:
        throw MergeError.exportFailed("Export finished with status: \(exportSession.status.rawValue)")
    }
}

do {
    let args = try parseArguments()
    try merge(
        videoURL: args.videoURL,
        audioURL: args.audioURL,
        outputURL: args.outputURL,
        replace: args.replace
    )
    print("merged: \(args.outputURL.path)")
} catch {
    fputs("\(error)\n", stderr)
    exit(1)
}
