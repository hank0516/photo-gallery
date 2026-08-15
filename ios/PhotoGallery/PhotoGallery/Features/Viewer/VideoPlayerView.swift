import AVKit
import SwiftUI

struct VideoPlayerView: View {
    let itemId: Int
    @State private var player: AVPlayer?
    @State private var isLoading = true
    @State private var error: String?

    var body: some View {
        Group {
            if let player {
                VideoPlayer(player: player)
                    .ignoresSafeArea()
            } else if isLoading {
                ProgressView()
                    .tint(.white)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color.black)
            } else if let error {
                Text(error)
                    .foregroundStyle(.white)
                    .multilineTextAlignment(.center)
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color.black)
            }
        }
        .task { await loadVideo() }
        .onDisappear { player?.pause() }
    }

    private func loadVideo() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let detail: PhotoDetail = try await APIClient.shared.fetch(Endpoints.photo(itemId))
            let p = AVPlayer(url: detail.originalURL)
            player = p
            p.play()
        } catch {
            self.error = error.localizedDescription
        }
    }
}
