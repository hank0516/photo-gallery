import Foundation
import Observation

// Photo item as returned by GET /albums/{id}
struct AlbumPhoto: Decodable, Identifiable {
    let id: Int
    let filename: String
    let caption: String?
    let mimeType: String?
    let thumb300URL: URL?
    let thumb800URL: URL?
    let width: Int?
    let height: Int?
    let exifDateTaken: String?

    var isVideo: Bool {
        mimeType?.hasPrefix("video/") ?? false
    }

    enum CodingKeys: String, CodingKey {
        case id, filename, caption, width, height
        case mimeType      = "mime_type"
        case thumb300URL   = "thumb_300_url"
        case thumb800URL   = "thumb_800_url"
        case exifDateTaken = "exif_date_taken"
    }
}

struct AlbumDetailResponse: Decodable {
    let album: AlbumInfo
    let photos: [AlbumPhoto]
    let total: Int
    let page: Int
    let perPage: Int
    let locked: Bool?

    enum CodingKeys: String, CodingKey {
        case album, photos, total, page, locked
        case perPage = "per_page"
    }
}

struct AlbumInfo: Decodable {
    let id: Int
    let name: String
    let myRole: String
    let isLocked: Bool

    enum CodingKeys: String, CodingKey {
        case id, name
        case myRole   = "my_role"
        case isLocked = "is_locked"
    }
}

@MainActor
@Observable
final class AlbumDetailViewModel {
    let album: Album
    var photos: [AlbumPhoto] = []
    var isLoading = false
    var error: String?
    var hasMore = true
    var isLocked = false
    private var currentPage = 0
    private let perPage = 50

    init(album: Album) {
        self.album = album
        self.isLocked = album.isLocked
    }

    func loadNextPage() async {
        guard !isLoading && hasMore && !isLocked else { return }
        isLoading = true
        error = nil
        defer { isLoading = false }
        let nextPage = currentPage + 1
        let url = "\(Endpoints.album(album.id))?page=\(nextPage)&per_page=\(perPage)"
        do {
            let response: AlbumDetailResponse = try await APIClient.shared.fetch(url)
            if response.locked == true {
                isLocked = true
                return
            }
            photos.append(contentsOf: response.photos)
            currentPage = nextPage
            hasMore = photos.count < response.total
        } catch {
            self.error = error.localizedDescription
        }
    }

    func reset() {
        photos = []
        currentPage = 0
        hasMore = true
        isLocked = album.isLocked
    }
}
