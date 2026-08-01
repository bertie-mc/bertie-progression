package com.berlord.bertie_progression;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;

class ResourceDataTest {

    private static final Path RESOURCES = Path.of(System.getProperty("bertie.projectDir"),
            "src", "main", "resources");

    @Test
    void everyJsonResourceParses() throws IOException {
        List<String> failures = new ArrayList<>();
        long count;
        try (var files = Files.walk(RESOURCES)) {
            List<Path> jsonFiles = files.filter(path -> path.toString().endsWith(".json")).toList();
            count = jsonFiles.size();
            for (Path path : jsonFiles) {
                try {
                    JsonParser.parseString(Files.readString(path));
                } catch (RuntimeException failure) {
                    failures.add(RESOURCES.relativize(path) + ": " + failure.getMessage());
                }
            }
        }
        assertTrue(count >= 700, "expected the progression data set, found " + count + " JSON files");
        assertTrue(failures.isEmpty(), String.join("\n", failures));
    }

    @Test
    void localItemTextureReferencesExist() throws IOException {
        Path models = RESOURCES.resolve("assets/bertie_progression/models/item");
        List<String> missing = new ArrayList<>();
        try (var files = Files.walk(models)) {
            for (Path model : files.filter(path -> path.toString().endsWith(".json")).toList()) {
                JsonElement parsed = JsonParser.parseString(Files.readString(model));
                if (!parsed.getAsJsonObject().has("textures")) {
                    continue;
                }
                for (JsonElement texture : parsed.getAsJsonObject().getAsJsonObject("textures").asMap().values()) {
                    String id = texture.getAsString();
                    if (!id.startsWith("bertie_progression:")) {
                        continue;
                    }
                    Path image = RESOURCES.resolve("assets/bertie_progression/textures/")
                            .resolve(id.substring("bertie_progression:".length()) + ".png");
                    if (!Files.isRegularFile(image)) {
                        missing.add(RESOURCES.relativize(model) + " -> " + RESOURCES.relativize(image));
                    }
                }
            }
        }
        assertTrue(missing.isEmpty(), String.join("\n", missing));
    }
}
