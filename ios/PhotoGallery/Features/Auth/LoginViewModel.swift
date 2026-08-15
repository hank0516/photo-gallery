import Observation

@Observable
final class LoginViewModel {
    var isLoading = false
    var errorMessage: String?

    func signIn(appState: AppState) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            let token = try await AuthService.shared.signIn()
            appState.setSession(token: token)
        } catch AuthError.cancelled {
            // User cancelled — no error shown
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
