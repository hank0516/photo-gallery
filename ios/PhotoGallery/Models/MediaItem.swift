import Foundation

enum MediaType: String, Codable {
    case photo, video
}

struct MediaItem: Codable, Identifiable {
    let id: Int
    let filename: String
    let caption: String?
    let mediaType: MediaType
    let thumbURL: URL
    let width: Int?
    let height: Int?
    let fileSizeBytes: Int?
    let uploadedAt: String

    // Populated on detail fetch
    var originalURL: URL?
    var exif: EXIFData?

    enum CodingKeys: String, CodingKey {
        case id, filename, caption
        case mediaType    = "media_type"
        case thumbURL     = "thumb_url"
        case width, height
        case fileSizeBytes = "file_size_bytes"
        case uploadedAt   = "uploaded_at"
        case originalURL  = "original_url"
        case exif
    }
}

struct MediaDetail: Codable {
    let id: Int
    let filename: String
    let caption: String?
    let mediaType: MediaType
    let originalURL: URL
    let thumbURL: URL
    let width: Int?
    let height: Int?
    let fileSizeBytes: Int?
    let exifTakenAt: String?
    let exifCameraModel: String?
    let exifLatitude: Double?
    let exifLongitude: Double?
    let uploadedAt: String

    enum CodingKeys: String, CodingKey {
        case id, filename, caption
        case mediaType      = "media_type"
        case originalURL    = "original_url"
        case thumbURL       = "thumb_url"
        case width, height
        case fileSizeBytes  = "file_size_bytes"
        case exifTakenAt    = "exif_taken_at"
        case exifCameraModel = "exif_camera_model"
        case exifLatitude   = "exif_latitude"
        case exifLongitude  = "exif_longitude"
        case uploadedAt     = "uploaded_at"
    }
}
