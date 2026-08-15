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

struct SearchPage: Decodable {
    let results: [SearchResult]
    let total: Int
    let page: Int
    let perPage: Int

    enum CodingKeys: String, CodingKey {
        case results, total, page
        case perPage = "per_page"
    }
}
