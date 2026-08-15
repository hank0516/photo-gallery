import AuthenticationServices
import Foundation

enum AuthError: Error, LocalizedError {
    case cancelled
    case missingToken
    case invalidCallback

    var errorDescription: String? {
        switch self {
        case .cancelled:        return "Sign-in was cancelled."
        case .missingToken:     return "No token received from server."
        case .invalidCallback:  return "Invalid callback URL."
        }
    }
}

@MainActor
final class AuthService: NSObject {
    static let shared = AuthService()
    private override init() {}

    func signIn() async throws -> String {
        guard let loginURL = URL(string: Endpoints.authLogin) else {
            throw AuthError.invalidCallback
        }
        let callbackScheme = "photogallery"

        return try await withCheckedThrowingContinuation { continuation in
            let session = ASWebAuthenticationSession(
                url: loginURL,
                callbackURLScheme: callbackScheme
            ) { callbackURL, error in
                if let error {
                    if (error as? ASWebAuthenticationSessionError)?.code == .canceledLogin {
                        continuation.resume(throwing: AuthError.cancelled)
                    } else {
                        continuation.resume(throwing: error)
                    }
                    return
                }
                guard let callbackURL,
                      let components = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false),
                      let token = components.queryItems?.first(where: { $0.name == "token" })?.value
                else {
                    continuation.resume(throwing: AuthError.missingToken)
                    return
                }
                continuation.resume(returning: token)
            }
            session.presentationContextProvider = self
            session.prefersEphemeralWebBrowserSession = false
            session.start()
        }
    }

    func signOut() async {
        await APIClient.shared.postVoid(Endpoints.authLogout)
        KeychainHelper.deleteToken()
    }
}

extension AuthService: ASWebAuthenticationPresentationContextProviding {
    nonisolated func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        ASPresentationAnchor()
    }
}
