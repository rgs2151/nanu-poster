from pathlib import Path

import imageio_ffmpeg
import matplotlib.pyplot as plt
import numpy as np


def display_limits(images):
    return np.percentile(images, [1.0, 99.8])


def create_dual_channel_figure(
    motor_view,
    rail_view,
    motor_limits,
    rail_limits,
    title,
    clock_text=None,
):
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["mathtext.fontset"] = "cm"
    plt.rcParams["image.interpolation"] = "none"
    plt.rcParams["figure.dpi"] = 150
    plt.rcParams["savefig.dpi"] = 300
    plt.rcParams["savefig.facecolor"] = "white"
    plt.rcParams["savefig.transparent"] = False

    fig = plt.figure(figsize=(6.2, 4.2))
    panel_centres = [0.25, 0.75]
    panel_bottom = 0.13
    panel_height = 0.68
    axes = []
    for centre, image in zip(panel_centres, [motor_view, rail_view]):
        panel_width = (
            panel_height
            * image.shape[1]
            / image.shape[0]
            * fig.get_figheight()
            / fig.get_figwidth()
        )
        axes.append(
            fig.add_axes(
                [centre - panel_width / 2, panel_bottom, panel_width, panel_height]
            )
        )

    image_artists = []
    for ax, image, panel_title, limits in zip(
        axes,
        [motor_view, rail_view],
        ["Motor proteins", "DNA rails"],
        [motor_limits, rail_limits],
    ):
        image_artist = ax.imshow(
            image,
            cmap="gray",
            vmin=limits[0],
            vmax=limits[1],
            interpolation="none",
            aspect="auto",
        )
        image_artists.append(image_artist)
        ax.set_title(panel_title, fontsize=11)
        ax.set_axis_off()

    fig.suptitle(title, fontsize=12, y=0.98)
    clock_artist = None
    if clock_text is not None:
        clock_artist = fig.text(
            0.5,
            0.035,
            clock_text,
            ha="center",
            va="bottom",
            fontsize=11,
        )
    return fig, image_artists, clock_artist


def format_elapsed_time(elapsed_minutes):
    total_seconds = int(round(elapsed_minutes * 60))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"Elapsed time {hours:02d}:{minutes:02d}:{seconds:02d}"


def write_dual_channel_video(
    motor_frames,
    rail_frames,
    elapsed_minutes,
    title,
    output_path,
    fps,
):
    motor_limits = display_limits(motor_frames)
    rail_limits = display_limits(rail_frames)
    writer = None
    for motor_frame, rail_frame, elapsed_minute in zip(
        motor_frames,
        rail_frames,
        elapsed_minutes,
    ):
        fig, _, _ = create_dual_channel_figure(
            motor_frame,
            rail_frame,
            motor_limits,
            rail_limits,
            title,
            format_elapsed_time(elapsed_minute),
        )
        fig.canvas.draw()
        rendered_frame = np.asarray(fig.canvas.buffer_rgba()).copy()
        if writer is None:
            height, width = rendered_frame.shape[:2]
            writer = imageio_ffmpeg.write_frames(
                Path(output_path),
                (width, height),
                pix_fmt_in="rgba",
                pix_fmt_out="yuv420p",
                fps=fps,
                codec="libx264",
                macro_block_size=2,
                output_params=["-crf", "18"],
            )
            writer.send(None)
        writer.send(rendered_frame.tobytes())
        plt.close(fig)
    writer.close()
