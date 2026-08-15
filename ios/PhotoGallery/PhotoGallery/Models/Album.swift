import Foundation

struct Album: Codable, Identifiable, Hashable {
    let id: Int
    let name: String
    let description: String?
    let albumDate: String?
    let coverThumbURL: URL?
    let photoCount: Int
    let myRole: String
    let isLocked: Bool
    let createdAt: String

    // Format "2025-07-15" → "2025.07.15"
    var formattedDate: String? {
        albumDate?.replacingOccurrences(of: "-", with: ".")
    }

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
