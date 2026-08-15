import Observation

@MainActor
@Observable
final class AlbumListViewModel {
    var albums: [Album] = []
    var isLoading = false
    var error: String?

    func load() async {
        isLoading = true
        error = nil
        defer { isLoading = false }
        do {
            let all: [Album] = try await APIClient.shared.fetch(Endpoints.albums)
            albums = all.filter { !$0.isLocked }
        } catch {
            self.error = error.localizedDescription
        }
    }
}
