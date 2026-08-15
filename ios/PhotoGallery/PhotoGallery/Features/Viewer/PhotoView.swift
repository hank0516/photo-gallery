import Kingfisher
import SwiftUI

struct PhotoView: View {
    let photo: AlbumPhoto
    @State private var displayURL: URL?
    @State private var scale: CGFloat = 1
    @State private var offset: CGSize = .zero
    @State private var lastScale: CGFloat = 1

    var body: some View {
        KFImage(source: displayURL.map { ImageCache.source(for: $0) })
            .placeholder { Color.black }
            .resizable()
            .scaledToFit()
            .scaleEffect(scale)
            .offset(offset)
            .gesture(magnifyGesture)
            .simultaneousGesture(dragGesture)
            .onTapGesture(count: 2) { resetZoom() }
            .animation(.spring(duration: 0.3), value: scale)
            .task { await loadProgressive() }
    }

    private var magnifyGesture: some Gesture {
        MagnificationGesture()
            .onChanged { scale = max(1, lastScale * $0) }
            .onEnded { _ in
                lastScale = scale
                if scale < 1 { resetZoom() }
            }
    }

    private var dragGesture: some Gesture {
        DragGesture()
            .onChanged { if scale > 1 { offset = $0.translation } }
            .onEnded { _ in if scale <= 1 { resetZoom() } }
    }

    private func resetZoom() {
        scale = 1; lastScale = 1; offset = .zero
    }

    private func loadProgressive() async {
        // Step 1: show thumb_800 immediately (likely already cached)
        displayURL = photo.thumb800URL ?? photo.thumb300URL

        // Step 2: fetch original_url from /photos/{id}
        guard let detail = try? await APIClient.shared.fetch(
            Endpoints.photo(photo.id)) as PhotoDetail
        else { return }

        // Step 3: pre-load original into cache, then swap
        let source = ImageCache.source(for: detail.originalURL)
        await withCheckedContinuation { (continuation: CheckedContinuation<Void, Never>) in
            KingfisherManager.shared.retrieveImage(with: source) { _ in
                continuation.resume()
            }
        }
        displayURL = detail.originalURL
    }
}
