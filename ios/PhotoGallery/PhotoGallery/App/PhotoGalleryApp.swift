import SwiftUI

@main
struct PhotoGalleryApp: App {
    @State private var appState = AppState()

    init() {
        ImageCache.configure()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(appState)
                .onOpenURL { url in
                    handleCallback(url: url)
                }
        }
    }

    private func handleCallback(url: URL) {
        guard url.scheme == "photogallery",
              url.host == "auth",
              url.path == "/callback",
              let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let token = components.queryItems?.first(where: { $0.name == "token" })?.value
        else { return }
        appState.setSession(token: token)
    }
}

struct ContentView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        if appState.session != nil {
            AlbumListView()
        } else {
            LoginView()
        }
    }
}
