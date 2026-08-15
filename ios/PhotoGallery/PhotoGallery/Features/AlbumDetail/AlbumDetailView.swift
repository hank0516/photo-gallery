import SwiftUI

struct AlbumDetailView: View {
    let album: Album
    @State private var vm: AlbumDetailViewModel
    @State private var viewerIndex: Int?

    init(album: Album) {
        self.album = album
        _vm = State(initialValue: AlbumDetailViewModel(album: album))
    }

    var body: some View {
        Group {
            if vm.isLoading && vm.photos.isEmpty {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let err = vm.error, vm.photos.isEmpty {
                ErrorBanner(message: err) {
                    Task { await vm.loadNextPage() }
                }
            } else {
                ScrollView {
                    MediaGrid(items: vm.photos, onTap: { index in
                        viewerIndex = index
                    }, onLoadMore: {
                        await vm.loadNextPage()
                    })
                    .padding(.horizontal, 12)
                    .padding(.bottom, 16)
                }
                .refreshable {
                    vm.reset()
                    await vm.loadNextPage()
                }
            }
        }
        .navigationTitle(album.name)
        .navigationBarTitleDisplayMode(.large)
        .task { await vm.loadNextPage() }
        .fullScreenCover(item: $viewerIndex) { index in
            MediaViewerView(photos: vm.photos, initialIndex: index)
        }
    }
}

extension Int: @retroactive Identifiable {
    public var id: Int { self }
}
