import PhotosUI
import SwiftUI
import UniformTypeIdentifiers

struct VideoFile: Transferable {
    let url: URL
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(contentType: .movie) { VideoFile(url: $0.url) }
    }
}

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
        let isVideo: Bool
        let ext: String      // e.g. "JPG", "MP4"
        var fileSize: Int64 = 0
        var status: Status = .pending

        enum Status { case pending, uploading, done, failed(String) }

        var displayName: String { "\(isVideo ? "影片" : "照片")  .\(ext.lowercased())" }

        var fileSizeString: String {
            guard fileSize > 0 else { return "" }
            return String(format: "%.1f MB", Double(fileSize) / 1_048_576)
        }
    }

    private var pendingCount: Int {
        uploadQueue.filter { if case .pending = $0.status { return true }; return false }.count
    }

    private var allDone: Bool {
        !uploadQueue.isEmpty && uploadQueue.allSatisfy {
            if case .done = $0.status { return true }; return false
        }
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
                        HStack(spacing: 10) {
                            Group {
                                switch item.status {
                                case .pending:
                                    Image(systemName: "circle").foregroundStyle(.secondary)
                                case .uploading:
                                    ProgressView().scaleEffect(0.8)
                                case .done:
                                    Image(systemName: "checkmark.circle.fill").foregroundStyle(.green)
                                case .failed:
                                    Image(systemName: "xmark.circle.fill").foregroundStyle(.red)
                                }
                            }
                            .frame(width: 22)

                            VStack(alignment: .leading, spacing: 2) {
                                Text(item.displayName).font(.subheadline)
                                HStack(spacing: 8) {
                                    if !item.fileSizeString.isEmpty {
                                        Text(item.fileSizeString).font(.caption).foregroundStyle(.secondary)
                                    }
                                    if case .failed(let e) = item.status {
                                        Text(e).font(.caption).foregroundStyle(.red).lineLimit(2)
                                    }
                                }
                            }
                        }
                    }
                }

                Spacer()

                Group {
                    if allDone {
                        Button("完成") { onUploaded(); dismiss() }
                            .buttonStyle(.borderedProminent)
                    } else if !uploadQueue.isEmpty && !isUploading && pendingCount > 0 {
                        Button { Task { await startUpload() } } label: {
                            Text("上傳 \(pendingCount) 個項目").frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .padding(.horizontal)
            }
            .padding(.top)
            .navigationTitle("上傳")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("關閉") { if !isUploading { dismiss() } }
                }
            }
            .onChange(of: selectedItems) { _, newItems in
                uploadQueue = newItems.map { pickerItem in
                    let types = pickerItem.supportedContentTypes
                    let isVideo = types.contains { $0.conforms(to: .movie) || $0.conforms(to: .video) || $0.conforms(to: .audiovisualContent) }
                    let ext = (types.first?.preferredFilenameExtension ?? (isVideo ? "mp4" : "jpg")).uppercased()
                    return UploadItem(item: pickerItem, isVideo: isVideo, ext: ext)
                }
            }
        }
    }

    private func startUpload() async {
        isUploading = true
        defer { isUploading = false }

        for i in uploadQueue.indices {
            guard case .pending = uploadQueue[i].status else { continue }
            uploadQueue[i].status = .uploading

            do {
                let pickerItem = uploadQueue[i].item
                let isVideo = uploadQueue[i].isVideo
                let rawExt = (pickerItem.supportedContentTypes.first?.preferredFilenameExtension ?? (isVideo ? "mp4" : "jpg")).lowercased()

                if isVideo {
                    guard let videoFile = try? await pickerItem.loadTransferable(type: VideoFile.self) else {
                        uploadQueue[i].status = .failed("無法讀取影片")
                        continue
                    }
                    let data = try Data(contentsOf: videoFile.url)
                    uploadQueue[i].fileSize = Int64(data.count)
                    let mime = rawExt == "mov" ? "video/quicktime" : "video/mp4"
                    _ = try await APIClient.shared.uploadPhoto(
                        albumId: albumId, imageData: data,
                        mimeType: mime, filename: "video.\(rawExt)")
                } else {
                    guard let data = try? await pickerItem.loadTransferable(type: Data.self) else {
                        uploadQueue[i].status = .failed("無法讀取照片")
                        continue
                    }
                    uploadQueue[i].fileSize = Int64(data.count)
                    _ = try await APIClient.shared.uploadPhoto(
                        albumId: albumId, imageData: data,
                        mimeType: "image/jpeg", filename: "photo.\(rawExt)")
                }
                uploadQueue[i].status = .done
            } catch {
                uploadQueue[i].status = .failed(error.localizedDescription)
            }
        }
        isUploading = false
    }
}
