import SwiftUI

struct AlbumDetailView: View {
    let album: Album
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss
    @State private var vm: AlbumDetailViewModel
    @State private var viewerIndex: Int?
    @State private var showUpload = false
    @State private var showMembers = false
    @State private var isDeleting = false

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
        .toolbar { adminToolbar }
        .task { await vm.loadNextPage() }
        .fullScreenCover(item: $viewerIndex) { index in
            MediaViewerView(photos: vm.photos, initialIndex: index) { deletedId in
                vm.photos.removeAll { $0.id == deletedId }
            }
        }
        .sheet(isPresented: $showUpload) {
            UploadView(albumId: album.id) {
                vm.reset()
                Task { await vm.loadNextPage() }
            }
        }
        .sheet(isPresented: $showMembers) {
            MembersView(album: album)
        }
    }

    @ToolbarContentBuilder
    private var adminToolbar: some ToolbarContent {
        if appState.session?.isAdmin == true {
            ToolbarItem(placement: .topBarTrailing) {
                Menu {
                    Button { showUpload = true } label: {
                        Label("上傳照片", systemImage: "arrow.up.circle")
                    }
                    Button { showMembers = true } label: {
                        Label("管理成員", systemImage: "person.2")
                    }
                    if let url = URL(string: Endpoints.albumDownloadZip(album.id) + "?token=\(KeychainHelper.loadToken() ?? "")") {
                        ShareLink(item: url) {
                            Label("下載相簿 ZIP", systemImage: "arrow.down.circle")
                        }
                    }
                    Divider()
                    Button(role: .destructive) {
                        Task { await deleteAlbum() }
                    } label: {
                        Label(isDeleting ? "刪除中…" : "刪除相簿", systemImage: "trash")
                    }
                    .disabled(isDeleting)
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
            }
        }
    }

    private func deleteAlbum() async {
        isDeleting = true
        defer { isDeleting = false }
        do {
            try await APIClient.shared.delete(Endpoints.album(album.id))
            dismiss()
        } catch {
            // error shown implicitly via isDeleting reset
        }
    }
}

extension Int: @retroactive Identifiable {
    public var id: Int { self }
}
