from PIL import Image


def replace_color(image_path, target_color, replacement_color, output_path):
    # Open the image
    img = Image.open(image_path).convert('RGBA')
    datas = img.getdata()

    # Replace the target color with the replacement color
    new_data = []
    for item in datas:
        # Change all target colors to replacement color
        if item[:3] == target_color:
            new_data.append(replacement_color + (item[3],))  # Retaining the original alpha channel
        else:
            new_data.append(item)

    # Update image data
    img.putdata(new_data)

    # Save the modified image
    img.save(output_path)


# Example usage
if __name__ == "__main__":
    image_path = "assets/entities/AnimationSheet_Character.png"
    target_color = (0, 0, 0)  # Red color
    replacement_color = (1, 1, 1)  # Green color
    output_path = "output_image.png"

    replace_color(image_path, target_color, replacement_color, output_path)
    print(f"Image saved as {output_path}")
