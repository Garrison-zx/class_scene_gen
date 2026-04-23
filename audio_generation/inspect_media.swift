import AVFoundation
import Foundation

guard CommandLine.arguments.count == 2 else {
    fputs("Usage: swift inspect_media.swift <media-file>\n", stderr)
    exit(1)
}

let url = URL(fileURLWithPath: CommandLine.arguments[1])
let asset = AVURLAsset(url: url)

let videoTracks = asset.tracks(withMediaType: .video)
let audioTracks = asset.tracks(withMediaType: .audio)
let durationSeconds = CMTimeGetSeconds(asset.duration)

print("path=\(url.path)")
print("duration_seconds=\(durationSeconds)")
print("video_tracks=\(videoTracks.count)")
print("audio_tracks=\(audioTracks.count)")

for (index, track) in audioTracks.enumerated() {
    print("audio[\(index)].enabled=\(track.isEnabled)")
    print("audio[\(index)].naturalTimeScale=\(track.naturalTimeScale)")
    print("audio[\(index)].timeRangeSeconds=\(CMTimeGetSeconds(track.timeRange.duration))")
    let descriptions = track.formatDescriptions as! [CMFormatDescription]
    for (descIndex, desc) in descriptions.enumerated() {
        let mediaSubType = CMFormatDescriptionGetMediaSubType(desc)
        let fourCC = String(format: "%c%c%c%c",
                            (mediaSubType >> 24) & 255,
                            (mediaSubType >> 16) & 255,
                            (mediaSubType >> 8) & 255,
                            mediaSubType & 255)
        print("audio[\(index)].format[\(descIndex)]=\(fourCC)")
    }
}
