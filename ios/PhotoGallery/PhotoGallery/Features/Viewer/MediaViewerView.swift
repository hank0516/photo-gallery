import SwiftUI

struct MediaViewerView: View {
    let photos: [AlbumPhoto]
    let initialIndex: Int
    var onDeleted: ((Int) -> Void)? = nil
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss
    @State private var currentIndex: Int
    @State private var isDeleting = false

    init(photos: [AlbumPhoto], initialIndex: Int, onDeleted: ((Int) -> Void)? = nil) {
        self.photos = photos
        self.initialIndex = initialIndex
        self.onDeleted = onDeleted
        _currentIndex = State(initialValue: initialIndex)
    }

    private var currentPhoto: AlbumPhoto? {
        guard currentIndex < photos.count else { return nil }
        return photos[currentIndex]
    }

    var body: some View {
        NavigationStack {
            TabView(selection: $currentIndex) {
                ForEach(Array(photos.enumerated()), id: \.element.id) { index, photo in
                    Group {
                        if photo.isVideo {
                            VideoPlayerView(itemId: photo.id)
                        } else {
                            PhotoView(photo: photo)
                        }
                    }
                    .tag(index)
                    .ignoresSafeArea()
                }
            }
            .tabViewStyle(.page(indexDisplayMode: .never))
            .background(Color.black)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark").foregroundStyle(.white)
                    }
                }
                ToolbarItem(placement: .principal) {
                    Text("\(currentIndex + 1) / \(photos.count)")
                        .foregroundStyle(.white)
                        .font(.subheadline)
                }
                if appState.session?.isAdmin == true {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button(role: .destructive) {
                            Task { await deleteCurrentPhoto() }
                        } label: {
                            if isDeleting {
                                ProgressView().tint(.white)
                            } else {
                                Image(systemName: "trash").foregroundStyle(.red)
                            }
                        }
                        .disabled(isDeleting)
                    }
                }
            }
            .toolbarBackground(.black.opacity(0.6), for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
        }
        .preferredColorScheme(.dark)
    }

    private func deleteCurrentPhoto() async {
        guard let photo = currentPhoto else { return }
        isDeleting = true
        defer { isDeleting = false }
        do {
            try await APIClient.shared.delete(Endpoints.photo(photo.id))
            onDeleted?(photo.id)
            if photos.count <= 1 {
                dismiss()
            } else {
                currentIndex = max(0, currentIndex - 1)
            }
        } catch {}
    }
}
