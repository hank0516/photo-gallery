import Kingfisher
import SwiftUI

struct MediaGrid: View {
    let items: [AlbumPhoto]
    let onTap: (Int) -> Void
    let onLoadMore: () async -> Void

    private let columns = [GridItem(.adaptive(minimum: 110), spacing: 4)]

    var body: some View {
        LazyVGrid(columns: columns, spacing: 4) {
            ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                Button { onTap(index) } label: {
                    Color.secondary.opacity(0.15)
                        .aspectRatio(1, contentMode: .fit)
                        .overlay(
                            KFImage(source: item.thumb300URL.map { ImageCache.source(for: $0) })
                                .resizable()
                                .scaledToFill()
                        )
                        .overlay(alignment: .bottomTrailing) {
                            if item.isVideo {
                                Image(systemName: "play.fill")
                                    .font(.caption)
                                    .padding(5)
                                    .background(.ultraThinMaterial, in: Circle())
                                    .padding(6)
                            }
                        }
                        .clipShape(Rectangle())
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
