import Kingfisher
import SwiftUI

struct PhotoView: View {
    let photo: AlbumPhoto
    @State private var originalURL: URL?
    @State private var scale: CGFloat = 1
    @State private var offset: CGSize = .zero   
    @State private var lastScale: CGFloat = 1

    private var thumbURL: URL? { photo.thumb800URL ?? photo.thumb300URL }

    var body: some View {
        KFImage(source: (originalURL ?? thumbURL).map { ImageCache.source(for: $0) })
            .placeholder {
                // Keep showing thumb while original downloads
                KFImage(source: thumbURL.map { ImageCache.source(for: $0) })
                    .resizable()
                    .scaledToFit()
            }
            .fade(duration: 0.25)
            .resizable()
            .scaledToFit()
            .scaleEffect(scale)
            .offset(offset)
            .gesture(magnifyGesture)
            .simultaneousGesture(dragGesture)
            .onTapGesture(count: 2) { resetZoom() }
            .task(id: photo.id) { await loadOriginal() }
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

    private func loadOriginal() async {
        guard let detail = try? await APIClient.shared.fetch(
            Endpoints.photo(photo.id)) as PhotoDetail
        else { return }
        originalURL = detail.originalURL
    }
}
