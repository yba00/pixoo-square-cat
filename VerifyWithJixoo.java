import io.github.glaforge.jixoo.image.ImageProcessor;
import io.github.glaforge.jixoo.image.ImageProcessor.ScaleMode;

import java.nio.file.Path;

/**
 * Checks, with Jixoo's own image code, that an upload lands on the Pixoo 64 pixel for pixel.
 *
 * <pre>
 *   java -cp jixoo64-0.3.0-cli.jar VerifyWithJixoo.java visuals/square_cat
 * </pre>
 *
 * Resizes {@code <name>_1024.png} to the 64x64 matrix the way {@code pixoo-cli image} does
 * and compares the LEDs with {@code <name>_64.png}.
 */
public class VerifyWithJixoo {

    public static void main(String[] args) {
        String name = args.length > 0 ? args[0] : "visuals/square_cat";
        byte[] shown = ImageProcessor.loadImage(Path.of(name + "_1024.png"))
                .resizeAndFit(64, 64, ScaleMode.FIT_CENTER)
                .toRawRgb();
        byte[] frame = ImageProcessor.loadImage(Path.of(name + "_64.png")).toRawRgb();

        int differing = 0;
        for (int i = 0; i < frame.length; i += 3) {
            if (shown[i] != frame[i] || shown[i + 1] != frame[i + 1] || shown[i + 2] != frame[i + 2]) {
                differing++;
            }
        }
        if (shown.length != frame.length || differing > 0) {
            System.out.printf("MISMATCH: %d of %d LEDs differ%n", differing, frame.length / 3);
            System.exit(1);
        }
        System.out.printf("OK: Jixoo shows %s_1024.png as exactly %s_64.png (%d LEDs)%n", name, name, frame.length / 3);
    }
}
