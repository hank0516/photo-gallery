import Foundation

enum APIError: Error, LocalizedError {
    case unauthorized
    case httpError(Int)
    case decodingError(Error)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .unauthorized:         return "Session expired. Please sign in again."
        case .httpError(let code):  return "Server error (\(code))."
        case .decodingError:        return "Unexpected response from server."
        case .networkError(let e):  return e.localizedDescription
        }
    }
}

@MainActor
final class APIClient {
    static let shared = APIClient()
    private let session = URLSession.shared
    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        return d
    }()

    // Called by AppState when session expires
    var onUnauthorized: (() -> Void)?

    private init() {}

    func fetch<T: Decodable>(_ urlString: String, method: String = "GET", body: Data? = nil, extraHeaders: [String: String] = [:]) async throws -> T {
        guard let url = URL(string: urlString) else {
            throw APIError.networkError(URLError(.badURL))
        }
        var request = URLRequest(url: url)
        request.httpMethod = method
        if let token = KeychainHelper.loadToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            request.httpBody = body
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        for (key, value) in extraHeaders {
            request.setValue(value, forHTTPHeaderField: key)
        }

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }

        if let http = response as? HTTPURLResponse {
            if http.statusCode == 401 {
                onUnauthorized?()
                throw APIError.unauthorized
            }
            guard (200..<300).contains(http.statusCode) else {
                throw APIError.httpError(http.statusCode)
            }
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    func post<T: Decodable>(_ urlString: String, body: Encodable) async throws -> T {
        let data = try JSONEncoder().encode(body)
        return try await fetch(urlString, method: "POST", body: data)
    }

    func postVoid(_ urlString: String) async throws {
        guard let url = URL(string: urlString) else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        if let token = KeychainHelper.loadToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        _ = try? await session.data(for: request)
    }

    func downloadData(from urlString: String) async throws -> Data {
        guard let url = URL(string: urlString) else {
            throw APIError.networkError(URLError(.badURL))
        }
        let (data, _) = try await session.data(from: url)
        return data
    }
}
