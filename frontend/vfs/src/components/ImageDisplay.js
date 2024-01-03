import React, { useState } from "react";

const ImageDisplay = ({ uid }) => {
  const [imageGroups, setImageGroups] = useState({});
  const [uploadedImages, setUploadedImages] = useState({});
  const [uploadedGroups, setUploadedGroups] = useState(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [isDownload, setIsDownload] = useState(false);

  const [currentGroupIndex, setCurrentGroupIndex] = useState(0);

  const groupKeys = Object.keys(imageGroups);
  const currentGroup = groupKeys[currentGroupIndex];

  const nextGroup = () => {
    if (currentGroupIndex < groupKeys.length - 1) {
      setCurrentGroupIndex(currentGroupIndex + 1);
    }
  };

  const previousGroup = () => {
    if (currentGroupIndex > 0) {
      setCurrentGroupIndex(currentGroupIndex - 1);
    }
  };

  const fetchImages = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/get_images/${uid}`);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      setImageGroups(data);
    } catch (error) {
      console.error("Could not fetch images:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (event, group) => {
    setUploadedImages({
      ...uploadedImages,
      [group]: event.target.files[0],
    });
  };

  const uploadImage = async (group) => {
    const formData = new FormData();
    formData.append("file", uploadedImages[group]);

    try {
      const response = await fetch(
        `http://localhost:8000/uploadnewfaces/${uid}/${group}`,
        {
          method: "POST",
          body: formData,
        }
      );
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      setUploadedGroups(new Set(uploadedGroups.add(group)));
      // fetchImages();
    } catch (error) {
      console.error("Could not upload image:", error);
    }
  };

  const downloadVideo = async () => {
    const response = await fetch(
      `http://localhost:8000/download_result_video/${uid}`
    );
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = uid + ".mp4";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);
  };

  const faceSwap = async () => {
    try {
      const groupIdsArray = Array.from(uploadedGroups).map(Number);
      console.log(groupIdsArray);
      const response = await fetch(`http://localhost:8000/faceswap/${uid}`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({ group_ids: groupIdsArray })
      });

      if (!response.ok) {
          const errorResponse = await response.json();
          console.error('Error Response:', errorResponse);
          throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Face swap response:', data);
      setIsDownload(true);
      // fetchImages();
    } catch (error) {
      console.error("Could not perform face swap:", error);
    }
  };
  return (
    <div className="space-y-4">
      <button
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition duration-300"
        onClick={fetchImages}
        disabled={isLoading}
      >
        {isLoading ? "Loading..." : "Load Images"}
      </button>

      {groupKeys.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-semibold">Group {currentGroup}</h3>
          <label
            htmlFor="new-face"
            className="block w-full px-4 py-2 bg-blue-600 text-white rounded cursor-pointer mb-2 transition-colors duration-300 hover:bg-blue-700"
          >
            Choose New Face
          </label>
          <input
            id="new-face"
            className="hidden"
            type="file"
            onChange={(event) => handleFileChange(event, currentGroup)}
          />
          <button
            className="ml-2 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition duration-300"
            onClick={() => uploadImage(currentGroup)}
          >
            Upload Image
          </button>
          <div className="flex flex-wrap gap-2">
            {imageGroups[currentGroup].map((image, idx) => (
              <img
                key={idx}
                src={`http://localhost:8000/images/${image}`}
                alt={`Group ${currentGroup} ${idx}`}
                className="w-14 h-14 object-cover"
              />
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-between mt-4">
        <button
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition duration-300"
          onClick={previousGroup}
          disabled={currentGroupIndex === 0}
        >
          Previous
        </button>
        <button
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition duration-300"
          onClick={nextGroup}
          disabled={currentGroupIndex === groupKeys.length - 1}
        >
          Next
        </button>
      </div>

      {uploadedGroups.size > 0 && (
        <button
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition duration-300"
          onClick={faceSwap}
        >
          Face Swap for Group {Array.from(uploadedGroups).join(", ")}
        </button>
      )}

      {isDownload && (
        <button
          className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 transition duration-300"
          onClick={downloadVideo}
        >
          Download
        </button>
      )}
    </div>
  );
};

export default ImageDisplay;
