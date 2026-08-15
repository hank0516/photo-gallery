import Foundation

struct Page<T: Decodable>: Decodable {
    let items: [T]
    let total: Int
    let page: Int
    let perPage: Int

    enum CodingKeys: String, CodingKey {
        case items = "photos"
        case total, page
        case perPage = "per_page"
    }
}

// Search response: GET /search returns { "photos": [...], "total": ..., "page": ..., "per_page": ... }
struct SearchPage: Decodable {
    let photos: [SearchPhoto]
    let total: Int
    let page: Int
    let perPage: Int

    enum CodingKeys: String, CodingKey {
        case photos, total, page
        case perPage = "per_page"
    }
}

// Photo item returned by GET /search (same as AlbumPhoto + album_id + album_name)
struct SearchPhoto: Decodable, Identifiable {
    let id: Int
    let filename: String
    let mimeType: String
    let caption: String?
    let thumb300URL: URL?
    let thumb800URL: URL?
    let exifDateTaken: String?
    let width: Int?
    let height: Int?
    let albumId: Int
    let albumName: String

    var isVideo: Bool { mimeType.hasPrefix("video/") }

    enum CodingKeys: String, CodingKey {
        case id, filename, caption, width, height
        case mimeType      = "mime_type"
        case thumb300URL   = "thumb_300_url"
        case thumb800URL   = "thumb_800_url"
        case exifDateTaken = "exif_date_taken"
        case albumId       = "album_id"
        case albumName     = "album_name"
    }
}
