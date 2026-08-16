import PhotosUI
import SwiftUI

struct UploadView: View {
    let albumId: Int
    var onUploaded: () -> Void
    @Environment(\.dismiss) private var dismiss

    @State private var selectedItems: [PhotosPickerItem] = []
    @State private var uploadQueue: [UploadItem] = []
    @State private var isUploading = false

    struct UploadItem: Identifiable {
        let id = UUID()
        let item: PhotosPickerItem
        var status: Status = .pending
        enum Status { case pending, uploading, done, failed(String) }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                PhotosPicker(selection: $selectedItems, maxSelectionCount: 30,
                             matching: .any(of: [.images, .videos])) {
                    Label("選擇照片 / 影片", systemImage: "photo.on.rectangle.angled")
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.accentColor.opacity(0.1), in: RoundedRectangle(cornerRadius: 12))
                }
                .padding(.horizontal)

                if !uploadQueue.isEmpty {
                    List(uploadQueue) { item in
                        HStack {
                            switch item.status {
                            case .pending:   Image(systemName: "circle").foregroundStyle(.secondary)
                            case .uploading: ProgressView().scaleEffect(0.8)
                            case .done:      Image(systemName: "checkmark.circle.fill").foregroundStyle(.green)
                            case .failed(let e):
                                Image(systemName: "xmark.circle.fill").foregroundStyle(.red)
                                Text(e).font(.caption).foregroundStyle(.red)
                            }
                            Text(item.item.itemIdentifier ?? "Photo").font(.caption).foregroundStyle(.secondary)
                        }
                    }
                }

                Spacer()

                if !uploadQueue.isEmpty && !isUploading {
                    Button {
                        Task { await startUpload() }
                    } label: {
                        Text("上傳 \(uploadQueue.filter { if case .pending = $0.status { return true }; return false }.count) 個項目")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .padding(.horizontal)
                }
            }
            .padding(.top)
            .navigationTitle("上傳")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("關閉") {
                        if !isUploading { dismiss() }
                    }
                }
            }
            .onChange(of: selectedItems) { _, newItems in
                uploadQueue = newItems.map { UploadItem(item: $0) }
            }
        }
    }

    private func startUpload() async {
        isUploading = true
        for i in uploadQueue.indices {
            guard case .pending = uploadQueue[i].status else { continue }
            uploadQueue[i].status = .uploading

            do {
                let pickerItem = uploadQueue[i].item
                // Load data from Photos
                guard let data = try await pickerItem.loadTransferable(type: Data.self) else {
                    uploadQueue[i].status = .failed("無法讀取檔案")
                    continue
                }
                let mimeType: String
                let filename: String
                if let type = pickerItem.supportedContentTypes.first {
                    if type.conforms(to: .movie) || type.conforms(to: .video) {
                        mimeType = "video/mp4"
                        filename = "video.mp4"
                    } else {
                        mimeType = "image/jpeg"
                        filename = "photo.jpg"
                    }
                } else {
                    mimeType = "image/jpeg"
                    filename = "photo.jpg"
                }

                _ = try await APIClient.shared.uploadPhoto(
                    albumId: albumId,
                    imageData: data,
                    mimeType: mimeType,
                    filename: filename)
                uploadQueue[i].status = .done
            } catch {
                uploadQueue[i].status = .failed(error.localizedDescription)
            }
        }
        isUploading = false
        let allDone = uploadQueue.allSatisfy {
            if case .done = $0.status { return true }; return false
        }
        if allDone {
            onUploaded()
            dismiss()
        }
    }
}
