import SwiftUI

struct LoginView: View {
    @Environment(AppState.self) private var appState
    @State private var vm = LoginViewModel()

    var body: some View {
        VStack(spacing: 32) {
            Spacer()
            Image(systemName: "photo.stack")
                .font(.system(size: 72))
                .foregroundStyle(.tint)
            Text("Photo Gallery")
                .font(.largeTitle.bold())

            if let msg = appState.sessionExpiredMessage {
                Text(msg)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }

            if vm.isLoading {
                ProgressView()
            } else {
                Button {
                    Task { await vm.signIn(appState: appState) }
                } label: {
                    Label("Sign in with Google", systemImage: "person.badge.key")
                        .frame(maxWidth: 280)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
            }

            if let err = vm.errorMessage {
                Text(err)
                    .foregroundStyle(.red)
                    .font(.caption)
            }
            Spacer()
        }
        .padding()
    }
}
