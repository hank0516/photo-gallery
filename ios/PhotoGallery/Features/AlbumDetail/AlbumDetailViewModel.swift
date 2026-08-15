import Observation

struct AlbumDetail: Decodable {
    let id: Int
    let name: String
    let myRole: String
    let isLocked: Bool
    let photos: [MediaItem]
    let total: Int
    let page: Int
    let perPage: Int

    enum CodingKeys: String, CodingKey {
        case id, name, photos, total, page
        case myRole  = "my_role"
        case isLocked = "is_locked"
        case perPage = "per_page"
    }
}

@Observable
final class AlbumDetailViewModel {
    let album: Album
    var items: [MediaItem] = []
    var isLoading = false
    var error: String?
    var hasMore = true
    private var currentPage = 0
    private let perPage = 50

    init(album: Album) { self.album = album }

    func loadNextPage() async {
        guard !isLoading && hasMore else { return }
        isLoading = true
        error = nil
        defer { isLoading = false }
        let nextPage = currentPage + 1
        let url = "\(Endpoints.album(album.id))?page=\(nextPage)&per_page=\(perPage)"
        do {
            let detail: AlbumDetail = try await APIClient.shared.fetch(url)
            items.append(contentsOf: detail.photos)
            currentPage = nextPage
            hasMore = items.count < detail.total
        } catch {
            self.error = error.localizedDescription
        }
    }

    func reset() {
        items = []
        currentPage = 0
        hasMore = true
    }
}
