import Foundation

struct Album: Codable, Identifiable {
    let id: Int
    let name: String
    let description: String?
    let albumDate: String?
    let coverThumbURL: URL?
    let photoCount: Int
    let myRole: String
    let isLocked: Bool
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, name, description
        case albumDate    = "album_date"
        case coverThumbURL = "cover_thumb_url"
        case photoCount   = "photo_count"
        case myRole       = "my_role"
        case isLocked     = "is_locked"
        case createdAt    = "created_at"
    }
}
