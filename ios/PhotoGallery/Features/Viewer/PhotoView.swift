import Kingfisher
import SwiftUI

struct PhotoView: View {
    let url: URL
    @State private var scale: CGFloat = 1
    @State private var offset: CGSize = .zero
    @State private var lastScale: CGFloat = 1

    var body: some View {
        KFImage(url)
            .resizable()
            .scaledToFit()
            .scaleEffect(scale)
            .offset(offset)
            .gesture(
                MagnificationGesture()
                    .onChanged { value in
                        scale = max(1, lastScale * value)
                    }
                    .onEnded { _ in
                        lastScale = scale
                        if scale < 1 { resetZoom() }
                    }
            )
            .simultaneousGesture(
                DragGesture()
                    .onChanged { value in
                        guard scale > 1 else { return }
                        offset = value.translation
                    }
                    .onEnded { _ in
                        if scale <= 1 { resetZoom() }
                    }
            )
            .onTapGesture(count: 2) { resetZoom() }
            .animation(.spring(duration: 0.3), value: scale)
    }

    private func resetZoom() {
        scale = 1
        lastScale = 1
        offset = .zero
    }
}
