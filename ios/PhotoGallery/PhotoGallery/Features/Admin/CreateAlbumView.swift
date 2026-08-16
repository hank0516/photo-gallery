import SwiftUI

struct CreateAlbumView: View {
    @Environment(\.dismiss) private var dismiss
    var onCreated: (Album) -> Void

    @State private var name = ""
    @State private var description = ""
    @State private var albumDate = Date()
    @State private var hasDate = false
    @State private var isLoading = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("相簿資訊") {
                    TextField("名稱", text: $name)
                    TextField("描述（選填）", text: $description)
                }
                Section {
                    Toggle("設定日期", isOn: $hasDate)
                    if hasDate {
                        DatePicker("日期", selection: $albumDate, displayedComponents: .date)
                    }
                }
                if let error { Text(error).foregroundStyle(.red).font(.caption) }
            }
            .navigationTitle("建立相簿")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    if isLoading {
                        ProgressView()
                    } else {
                        Button("建立") { Task { await create() } }
                            .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
                            .fontWeight(.semibold)
                    }
                }
            }
        }
    }

    private func create() async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        struct Body: Encodable {
            let name: String
            let description: String?
            let album_date: String?
        }
        let fmt = ISO8601DateFormatter()
        fmt.formatOptions = [.withFullDate, .withDashSeparatorInDate]
        let body = Body(
            name: name.trimmingCharacters(in: .whitespaces),
            description: description.isEmpty ? nil : description,
            album_date: hasDate ? fmt.string(from: albumDate) : nil
        )
        do {
            let album: Album = try await APIClient.shared.post(Endpoints.albums, body: body)
            onCreated(album)
            dismiss()
        } catch {
            self.error = error.localizedDescription
        }
    }
}
