import SwiftUI

struct AlbumListView: View {
    @Environment(AppState.self) private var appState
    @State private var vm = AlbumListViewModel()

    private let columns = [GridItem(.adaptive(minimum: 160), spacing: 14)]

    var body: some View {
        NavigationStack {
            content
                .navigationTitle("Albums")
                .toolbar { signOutButton }
                .navigationDestination(for: Album.self) { AlbumDetailView(album: $0) }
        }
        .task { await vm.load() }
    }

    @ViewBuilder
    private var content: some View {
        if vm.isLoading && vm.albums.isEmpty {
            ProgressView()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else if let err = vm.error {
            ErrorBanner(message: err) { Task { await vm.load() } }
        } else {
            albumGrid
        }
    }

    private var albumGrid: some View {
        ScrollView {
            LazyVGrid(columns: columns, spacing: 16) {
                ForEach(vm.albums) { album in
                    NavigationLink(value: album) { AlbumCard(album: album) }
                        .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
        .refreshable { await vm.load() }
    }

    private var signOutButton: some ToolbarContent {
        ToolbarItem(placement: .topBarTrailing) {
            Button("Sign Out", role: .destructive) {
                Task {
                    await AuthService.shared.signOut()
                    appState.signOut()
                }
            }
        }
    }
}
