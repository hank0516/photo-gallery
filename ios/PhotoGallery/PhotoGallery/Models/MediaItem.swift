import Foundation

// PhotoDetail matches GET /photos/{id} response
struct PhotoDetail: Decodable {
    let id: Int
    let albumId: Int
    let filename: String
    let mimeType: String?
    let caption: String?
    let originalURL: URL
    let thumb300URL: URL?
    let thumb800URL: URL?
    let fileSizeBytes: Int?
    let width: Int?
    let height: Int?
    let exifDateTaken: String?
    let exifCamera: String?       // was exif_camera_model — actual field: exif_camera
    let exifGpsLat: Double?       // actual field: exif_gps_lat
    let exifGpsLon: Double?       // actual field: exif_gps_lon
    let uploadedAt: String

    var isVideo: Bool { mimeType?.hasPrefix("video/") ?? false }

    enum CodingKeys: String, CodingKey {
        case id, filename, caption, width, height
        case albumId       = "album_id"
        case mimeType      = "mime_type"
        case originalURL   = "original_url"
        case thumb300URL   = "thumb_300_url"
        case thumb800URL   = "thumb_800_url"
        case fileSizeBytes = "file_size_bytes"
        case exifDateTaken = "exif_date_taken"
        case exifCamera    = "exif_camera"
        case exifGpsLat    = "exif_gps_lat"
        case exifGpsLon    = "exif_gps_lon"
        case uploadedAt    = "uploaded_at"
    }
}
