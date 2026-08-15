import SwiftUI

struct AlbumListView: View {
    @Environment(AppState.self) private var appState
    @State private var vm = AlbumListViewModel()

    private let columns = [GridItem(.adaptive(minimum: 160), spacing: 12)]

    var body: some View {
        NavigationStack {
            Group {
                if vm.isLoading && vm.albums.isEmpty {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let err = vm.error {
                    ErrorBanner(message: err) {
                        Task { await vm.load() }
                    }
                } else {
                    ScrollView {
                        LazyVGrid(columns: columns, spacing: 16) {
                            ForEach(vm.albums) { album in
                                NavigationLink(value: album) {
                                    AlbumCard(album: album)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding()
                    }
                    .refreshable { await vm.load() }
                }
            }
            .navigationTitle("Albums")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Sign Out", role: .destructive) {
                        Task {
                            await AuthService.shared.signOut()
                            appState.signOut()
                        }
                    }
                }
            }
            .navigationDestination(for: Album.self) { album in
                AlbumDetailView(album: album)
            }
        }
        .task { await vm.load() }
    }
}
