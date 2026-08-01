import org.gradle.api.DefaultTask
import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.provider.ListProperty
import org.gradle.api.tasks.CacheableTask
import org.gradle.api.tasks.Classpath
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.OutputDirectory
import org.gradle.api.tasks.TaskAction
import org.gradle.language.jvm.tasks.ProcessResources
import org.gradle.api.tasks.testing.Test
import java.util.zip.ZipFile

@CacheableTask
abstract class ExtractJarJarLibraries : DefaultTask() {
    @get:Classpath
    abstract val archives: ConfigurableFileCollection

    @get:Input
    abstract val libraryNames: ListProperty<String>

    @get:OutputDirectory
    abstract val destinationDirectory: DirectoryProperty

    @TaskAction
    fun extract() {
        val destination = destinationDirectory.get().asFile
        destination.deleteRecursively()
        destination.mkdirs()
        val wanted = libraryNames.get()
        archives.files.forEach { parent ->
            ZipFile(parent).use { archive ->
                archive.entries().asSequence()
                    .filter { entry ->
                        entry.name.startsWith("META-INF/jarjar/") &&
                            entry.name.endsWith(".jar") &&
                            wanted.any(entry.name::contains)
                    }
                    .forEach { entry ->
                        val target = destination.resolve(entry.name.substringAfterLast('/'))
                        archive.getInputStream(entry).use { input ->
                            target.outputStream().use(input::copyTo)
                        }
                        logger.lifecycle("extractJarJarLibs: extracted ${target.name} from ${parent.name}")
                    }
            }
        }
    }
}

plugins {
    `java-library`
    idea
    id("net.neoforged.moddev") version "2.0.134"
}

val minecraft_version: String by project
val minecraft_version_range: String by project
val neo_version: String by project
val neo_version_range: String by project
val loader_version_range: String by project
val parchment_mappings_version: String by project
val parchment_minecraft_version: String by project
val mod_id: String by project
val mod_name: String by project
val mod_license: String by project
val mod_version: String by project
val mod_group_id: String by project
val mod_authors: String by project
val mod_description: String by project

version = mod_version
group = mod_group_id

repositories {
    mavenLocal()
    maven { url = uri("https://api.modrinth.com/maven") }
}

base {
    archivesName = "bertie-progression"
}

java.toolchain.languageVersion = JavaLanguageVersion.of(21)

neoForge {
    version = neo_version

    parchment {
        mappingsVersion = parchment_mappings_version
        minecraftVersion = parchment_minecraft_version
    }

    runs {
        register("client") {
            client()
        }
        register("server") {
            server()
        }
        configureEach {
            systemProperty("forge.logging.markers", "REGISTRIES")
            logLevel = org.slf4j.event.Level.DEBUG
        }
    }

    mods {
        register(mod_id) {
            sourceSet(sourceSets.main.get())
        }
    }

    unitTest {
        enable()
        testedMod = mods.getByName(mod_id)
    }
}

// Ponder is embedded inside Create rather than published separately.
val jarJarParents by configurations.creating
val extractedLibsDir = layout.buildDirectory.dir("extracted-jarjar-libs").get().asFile

val extractJarJarLibs = tasks.register<ExtractJarJarLibraries>("extractJarJarLibs") {
    description = "Extract JarJar-embedded libraries (ponder, catnip) from parent mods onto the compile classpath."
    archives.from(jarJarParents)
    libraryNames.set(listOf("ponder-neoforge", "catnip"))
    destinationDirectory.set(layout.buildDirectory.dir("extracted-jarjar-libs"))
}

dependencies {
    compileOnly("maven.modrinth:create:6.0.10+mc1.21.1")
    add(jarJarParents.name, "maven.modrinth:create:6.0.10+mc1.21.1") // -> ponder-neoforge-1.0.82+mc1.21.1
    compileOnly(fileTree(extractedLibsDir) { include("*.jar") }.builtBy(extractJarJarLibs))

    testImplementation(platform("org.junit:junit-bom:6.1.2"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.named<Test>("test") {
    useJUnitPlatform()
    systemProperty("bertie.projectDir", layout.projectDirectory.asFile.absolutePath)
}

tasks.named("compileJava") {
    dependsOn(extractJarJarLibs)
}

val generateModMetadata = tasks.register<ProcessResources>("generateModMetadata") {
    val replaceProperties = mapOf(
        "minecraft_version" to minecraft_version,
        "minecraft_version_range" to minecraft_version_range,
        "neo_version" to neo_version,
        "neo_version_range" to neo_version_range,
        "loader_version_range" to loader_version_range,
        "mod_id" to mod_id,
        "mod_name" to mod_name,
        "mod_license" to mod_license,
        "mod_version" to mod_version,
        "mod_authors" to mod_authors,
        "mod_description" to mod_description,
    )
    inputs.properties(replaceProperties)
    expand(replaceProperties)
    from("src/main/templates")
    into("build/generated/sources/modMetadata")
}
sourceSets.main.get().resources.srcDir(generateModMetadata)
neoForge.ideSyncTask(generateModMetadata)
