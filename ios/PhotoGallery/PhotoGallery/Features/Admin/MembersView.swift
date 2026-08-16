import SwiftUI

struct AlbumMember: Decodable, Identifiable {
    var id: Int { userId }
    let userId: Int
    let email: String
    let name: String
    let role: String
    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case email, name, role
    }
}

struct AppUser: Decodable, Identifiable {
    let id: Int
    let email: String
    let name: String
}

struct MembersView: View {
    let album: Album
    @Environment(\.dismiss) private var dismiss

    @State private var members: [AlbumMember] = []
    @State private var allUsers: [AppUser] = []
    @State private var isLoading = true
    @State private var error: String?
    @State private var selectedUserId: Int? = nil
    @State private var selectedRole = "viewer"
    @State private var isAdding = false

    private var availableUsers: [AppUser] {
        let existingIds = Set(members.map { $0.userId })
        return allUsers.filter { !existingIds.contains($0.id) }
    }

    var body: some View {
        NavigationStack {
            List {
                if !members.isEmpty {
                    Section("目前成員") {
                        ForEach(members) { member in
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(member.name).font(.subheadline)
                                    Text(member.email).font(.caption).foregroundStyle(.secondary)
                                }
                                Spacer()
                                Picker("", selection: Binding(
                                    get: { member.role },
                                    set: { newRole in Task { await changeRole(member.userId, role: newRole) } }
                                )) {
                                    Text("viewer").tag("viewer")
                                    Text("uploader").tag("uploader")
                                    Text("admin").tag("admin")
                                }
                                .pickerStyle(.menu)
                            }
                            .swipeActions {
                                Button("移除", role: .destructive) {
                                    Task { await removeMember(member.userId) }
                                }
                            }
                        }
                    }
                }

                Section("新增成員") {
                    if availableUsers.isEmpty {
                        Text("沒有可新增的使用者").foregroundStyle(.secondary).font(.caption)
                    } else {
                        Picker("使用者", selection: $selectedUserId) {
                            Text("選擇使用者").tag(Optional<Int>.none)
                            ForEach(availableUsers) { user in
                                Text("\(user.name) (\(user.email))").tag(Optional(user.id))
                            }
                        }
                        Picker("角色", selection: $selectedRole) {
                            Text("viewer").tag("viewer")
                            Text("uploader").tag("uploader")
                            Text("admin").tag("admin")
                        }
                        Button(isAdding ? "新增中…" : "新增") {
                            Task { await addMember() }
                        }
                        .disabled(selectedUserId == nil || isAdding)
                    }
                }

                if let error { Text(error).foregroundStyle(.red).font(.caption) }
            }
            .navigationTitle("管理成員")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("完成") { dismiss() }
                }
            }
            .task { await loadData() }
            .overlay { if isLoading { ProgressView() } }
        }
    }

    private func loadData() async {
        isLoading = true
        defer { isLoading = false }
        async let membersResult: [AlbumMember] = APIClient.shared.fetch(Endpoints.albumPermissions(album.id))
        async let usersResult: [AppUser] = APIClient.shared.fetch(Endpoints.users)
        do {
            members = try await membersResult
            allUsers = try await usersResult
        } catch {
            self.error = error.localizedDescription
        }
    }

    private func changeRole(_ userId: Int, role: String) async {
        struct Body: Encodable { let role: String }
        do {
            let _: [String: String] = try await APIClient.shared.put(
                Endpoints.albumPermission(albumId: album.id, userId: userId),
                body: Body(role: role))
            if let i = members.firstIndex(where: { $0.userId == userId }) {
                members[i] = AlbumMember(userId: userId, email: members[i].email, name: members[i].name, role: role)
            }
        } catch { self.error = error.localizedDescription }
    }

    private func removeMember(_ userId: Int) async {
        do {
            try await APIClient.shared.delete(Endpoints.albumPermission(albumId: album.id, userId: userId))
            members.removeAll { $0.userId == userId }
        } catch { self.error = error.localizedDescription }
    }

    private func addMember() async {
        guard let userId = selectedUserId else { return }
        isAdding = true
        defer { isAdding = false }
        struct Body: Encodable { let role: String }
        do {
            let _: [String: String] = try await APIClient.shared.put(
                Endpoints.albumPermission(albumId: album.id, userId: userId),
                body: Body(role: selectedRole))
            await loadData()
            selectedUserId = nil
        } catch { self.error = error.localizedDescription }
    }
}
