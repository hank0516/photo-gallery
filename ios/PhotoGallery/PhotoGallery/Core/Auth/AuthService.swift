import AuthenticationServices
import Foundation
import UIKit

enum AuthError: Error, LocalizedError {
    case cancelled
    case missingToken
    case invalidCallback
    case sessionFailed

    var errorDescription: String? {
        switch self {
        case .cancelled:     return "Sign-in was cancelled."
        case .missingToken:  return "No token received from server."
        case .invalidCallback: return "Invalid callback URL."
        case .sessionFailed: return "Failed to start authentication session."
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

        return try await withCheckedThrowingContinuation { continuation in
            let session = ASWebAuthenticationSession(
                url: loginURL,
                callback: .customScheme("photogallery")
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
        try? await APIClient.shared.postVoid(Endpoints.authLogout)
        KeychainHelper.deleteToken()
    }
}

extension AuthService: ASWebAuthenticationPresentationContextProviding {
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first(where: { $0.activationState == .foregroundActive })?
            .keyWindow
        ?? UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .compactMap { $0.keyWindow }
            .first
        ?? UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first!
    }
}
