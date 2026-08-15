import Observation

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
            albums = try await APIClient.shared.fetch(Endpoints.albums)
        } catch {
            self.error = error.localizedDescription
        }
    }
}
