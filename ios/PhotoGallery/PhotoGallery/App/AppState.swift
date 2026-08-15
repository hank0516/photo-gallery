import Foundation
import Observation

struct Session {
    let token: String
    let userId: Int
    let email: String
    let isAdmin: Bool
}

@MainActor
@Observable
final class AppState {
    var session: Session?
    var sessionExpiredMessage: String?

    init() {
        // Restore session from Keychain on launch; validate with /auth/me async
        if let token = KeychainHelper.loadToken(), let session = decode(token: token) {
            self.session = session
            Task { @MainActor in await self.validateSession() }
        }
        APIClient.shared.onUnauthorized = { [weak self] in
            Task { @MainActor in
                self?.signOut(reason: "Session expired. Please sign in again.")
            }
        }
    }

    private func validateSession() async {
        struct Me: Decodable { let id: Int }
        do {
            let _: Me = try await APIClient.shared.fetch(Endpoints.authMe)
        } catch APIError.unauthorized {
            signOut(reason: "Session expired. Please sign in again.")
        } catch {
            // Network error — keep local session, will fail naturally on use
        }
    }

    func setSession(token: String) {
        guard let s = decode(token: token) else { return }
        KeychainHelper.save(token: token)
        session = s
        sessionExpiredMessage = nil
    }

    func signOut(reason: String? = nil) {
        KeychainHelper.deleteToken()
        session = nil
        sessionExpiredMessage = reason
    }

    private func decode(token: String) -> Session? {
        let parts = token.split(separator: ".")
        guard parts.count == 3 else { return nil }
        var base64 = String(parts[1])
        let rem = base64.count % 4
        if rem > 0 { base64 += String(repeating: "=", count: 4 - rem) }
        guard let data = Data(base64Encoded: base64),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let userId = json["user_id"] as? Int,
              let email  = json["email"]   as? String else { return nil }
        let isAdmin = json["is_admin"] as? Bool ?? false
        return Session(token: token, userId: userId, email: email, isAdmin: isAdmin)
    }
}
