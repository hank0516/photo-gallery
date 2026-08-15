import Foundation

enum Endpoints {
    static let baseURL = "https://cloud.hansu.tw/api/photo-gallery"

    static let authLogin    = "\(baseURL)/auth/login?redirect=native"
    static let authCallback = "\(baseURL)/auth/callback"
    static let authLogout   = "\(baseURL)/auth/logout"
    static let authMe       = "\(baseURL)/auth/me"

    static let albums       = "\(baseURL)/albums"
    static func album(_ id: Int) -> String { "\(baseURL)/albums/\(id)" }
    static func albumUnlock(_ id: Int) -> String { "\(baseURL)/albums/\(id)/unlock" }

    static func photo(_ id: Int) -> String { "\(baseURL)/photos/\(id)" }
    static func photoDownload(_ id: Int) -> String { "\(baseURL)/photos/\(id)/download" }

    static let search       = "\(baseURL)/search"
}
