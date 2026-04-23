import AVFoundation
import Foundation

enum AudioMergeError: Error, CustomStringConvertible {
    case usage(String)
    case missingTrack(String)
    case exportFailed(String)

    var description: String {
        switch self {
        case .usage(let message), .missingTrack(let message), .exportFailed(let message):
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
            if let value = iterator.next() { inputPaths.append(value) }
        case "--output":
            outputPath = iterator.next()
        case "--replace":
            replace = true
        default:
            throw AudioMergeError.usage("Unknown argument: \(arg)")
        }
    }

    guard !inputPaths.isEmpty, let outputPath else {
        throw AudioMergeError.usage("Usage: swift merge_audio_segments.swift --input <a1> --input <a2> ... --output <out.m4a> [--replace]")
    }

    return Arguments(
        inputURLs: inputPaths.map { URL(fileURLWithPath: $0) },
        outputURL: URL(fileURLWithPath: outputPath),
        replace: replace
    )
}

func merge(inputURLs: [URL], outputURL: URL, replace: Bool) throws {
    let fileManager = FileManager.default
    if replace, fileManager.fileExists(atPath: outputURL.path) {
        try fileManager.removeItem(at: outputURL)
    }
    try fileManager.createDirectory(at: outputURL.deletingLastPathComponent(), withIntermediateDirectories: true)

    let composition = AVMutableComposition()
    guard let compositionAudioTrack = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid) else {
        throw AudioMergeError.missingTrack("Unable to create composition audio track")
    }

    var insertAt = CMTime.zero
    for inputURL in inputURLs {
        let asset = AVURLAsset(url: inputURL)
        guard let sourceTrack = asset.tracks(withMediaType: .audio).first else {
            throw AudioMergeError.missingTrack("Missing audio track: \(inputURL.path)")
        }
        let duration = asset.duration
        try compositionAudioTrack.insertTimeRange(
            CMTimeRange(start: .zero, duration: duration),
            of: sourceTrack,
            at: insertAt
        )
        insertAt = CMTimeAdd(insertAt, duration)
    }

    guard let exportSession = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetAppleM4A) else {
        throw AudioMergeError.exportFailed("Unable to create audio export session")
    }
    exportSession.outputURL = outputURL
    exportSession.outputFileType = .m4a

    let semaphore = DispatchSemaphore(value: 0)
    exportSession.exportAsynchronously { semaphore.signal() }
    semaphore.wait()

    switch exportSession.status {
    case .completed:
        return
    case .failed:
        throw AudioMergeError.exportFailed(exportSession.error?.localizedDescription ?? "Unknown export failure")
    case .cancelled:
        throw AudioMergeError.exportFailed("Export cancelled")
    default:
        throw AudioMergeError.exportFailed("Export finished with status: \(exportSession.status.rawValue)")
    }
}

do {
    let args = try parseArguments()
    try merge(inputURLs: args.inputURLs, outputURL: args.outputURL, replace: args.replace)
    print("merged_audio: \(args.outputURL.path)")
} catch {
    fputs("\(error)\n", stderr)
    exit(1)
}
