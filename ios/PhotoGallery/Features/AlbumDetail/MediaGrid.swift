import Kingfisher
import SwiftUI

struct MediaGrid: View {
    let items: [MediaItem]
    let onTap: (Int) -> Void
    let onLoadMore: () async -> Void

    private let columns = [GridItem(.adaptive(minimum: 110), spacing: 2)]

    var body: some View {
        LazyVGrid(columns: columns, spacing: 2) {
            ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                Button { onTap(index) } label: {
                    ZStack(alignment: .bottomTrailing) {
                        KFImage(source: ImageCache.source(for: item.thumbURL))
                            .placeholder { Color.secondary.opacity(0.2) }
                            .resizable()
                            .scaledToFill()
                            .frame(minWidth: 0, maxWidth: .infinity)
                            .aspectRatio(1, contentMode: .fill)
                            .clipped()

                        if item.mediaType == .video {
                            Image(systemName: "play.fill")
                                .font(.caption)
                                .padding(5)
                                .background(.ultraThinMaterial, in: Circle())
                                .padding(6)
                        }
                    }
                }
                .buttonStyle(.plain)
                .onAppear {
                    if item.id == items.last?.id {
                        Task { await onLoadMore() }
                    }
                }
            }
        }
    }
}
