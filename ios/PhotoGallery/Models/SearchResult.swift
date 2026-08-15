import Foundation

struct SearchResult: Codable, Identifiable {
    var id: Int { item.id }
    let item: MediaItem
    let albumName: String

    enum CodingKeys: String, CodingKey {
        case albumName = "album_name"
        // MediaItem fields decoded flat
        case id, filename, caption
        case mediaType    = "media_type"
        case thumbURL     = "thumb_url"
        case width, height
        case fileSizeBytes = "file_size_bytes"
        case uploadedAt   = "uploaded_at"
        case albumId      = "album_id"
        case exifTakenAt  = "exif_taken_at"
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        albumName = try c.decode(String.self, forKey: .albumName)
        // Decode MediaItem fields directly from the flat search result
        let id           = try c.decode(Int.self, forKey: .id)
        let filename     = try c.decode(String.self, forKey: .filename)
        let caption      = try c.decodeIfPresent(String.self, forKey: .caption)
        let mediaType    = try c.decode(MediaType.self, forKey: .mediaType)
        let thumbURL     = try c.decode(URL.self, forKey: .thumbURL)
        item = MediaItem(
            id: id, filename: filename, caption: caption,
            mediaType: mediaType, thumbURL: thumbURL,
            width: nil, height: nil, fileSizeBytes: nil,
            uploadedAt: (try? c.decode(String.self, forKey: .uploadedAt)) ?? ""
        )
    }

    func encode(to encoder: Encoder) throws {}
}
