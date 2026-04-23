import AVFoundation
import Foundation

enum ConcatError: Error, CustomStringConvertible {
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
    let inputURLs: [URL]
    let outputURL: URL
    let replace: Bool
}

func parseArguments() throws -> Arguments {
    var inputPaths: [String] = []
    var outputPath: String?
    var replace = false

    var iterator = CommandLine.arguments.dropFirst().makeIterator()
    while let arg = iterator.next() {
        switch arg {
        case "--input":
            guard let value = iterator.next() else {
                throw ConcatError.usage("--input requires a path")
            }
            inputPaths.append(value)
        case "--output":
            outputPath = iterator.next()
        case "--replace":
            replace = true
        default:
            throw ConcatError.usage("Unknown argument: \(arg)")
        }
    }

    guard inputPaths.count >= 2, let outputPath else {
        throw ConcatError.usage("Usage: swift concat_videos.swift --input <clip1.mp4> --input <clip2.mp4> --output <out.mp4> [--replace]")
    }

    return Arguments(
        inputURLs: inputPaths.map { URL(fileURLWithPath: $0) },
        outputURL: URL(fileURLWithPath: outputPath),
        replace: replace
    )
}

func concat(inputURLs: [URL], outputURL: URL, replace: Bool) throws {
    let fileManager = FileManager.default
    if replace, fileManager.fileExists(atPath: outputURL.path) {
        try fileManager.removeItem(at: outputURL)
    }
    try fileManager.createDirectory(
        at: outputURL.deletingLastPathComponent(),
        withIntermediateDirectories: true
    )

    let composition = AVMutableComposition()
    guard let compositionVideoTrack = composition.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid) else {
        throw ConcatError.missingTrack("Unable to create composition video track")
    }
    let compositionAudioTrack = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)

    var cursor = CMTime.zero
    var preferredTransform = CGAffineTransform.identity

    for inputURL in inputURLs {
        let asset = AVURLAsset(url: inputURL)
        guard let sourceVideoTrack = asset.tracks(withMediaType: .video).first else {
            throw ConcatError.missingTrack("Missing video track: \(inputURL.path)")
        }

        let duration = asset.duration
        try compositionVideoTrack.insertTimeRange(
            CMTimeRange(start: .zero, duration: duration),
            of: sourceVideoTrack,
            at: cursor
        )

        if let sourceAudioTrack = asset.tracks(withMediaType: .audio).first {
            try compositionAudioTrack?.insertTimeRange(
                CMTimeRange(start: .zero, duration: duration),
                of: sourceAudioTrack,
                at: cursor
            )
        }

        if cursor == .zero {
            preferredTransform = sourceVideoTrack.preferredTransform
        }
        cursor = CMTimeAdd(cursor, duration)
    }

    compositionVideoTrack.preferredTransform = preferredTransform

    guard let exportSession = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetHighestQuality) else {
        throw ConcatError.exportFailed("Unable to create AVAssetExportSession")
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
        throw ConcatError.exportFailed(exportSession.error?.localizedDescription ?? "Unknown export failure")
    case .cancelled:
        throw ConcatError.exportFailed("Export cancelled")
    default:
        throw ConcatError.exportFailed("Export finished with status: \(exportSession.status.rawValue)")
    }
}

do {
    let args = try parseArguments()
    try concat(inputURLs: args.inputURLs, outputURL: args.outputURL, replace: args.replace)
    print("concatenated: \(args.outputURL.path)")
} catch {
    fputs("\(error)\n", stderr)
    exit(1)
}
