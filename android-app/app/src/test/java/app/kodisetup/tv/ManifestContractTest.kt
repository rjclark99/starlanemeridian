package app.kodisetup.tv

import kotlinx.serialization.json.*
import org.junit.Assert.assertEquals
import org.junit.Test

class ManifestContractTest {
    @Test fun exampleUsesSchemaOneAndDraftStage() {
        val manifest = listOf(java.io.File("../config/manifest.example.json"), java.io.File("../../config/manifest.example.json"))
            .first { it.isFile }
        val text = manifest.readText()
        val root = Json.parseToJsonElement(text).jsonObject
        assertEquals(1, root["schemaVersion"]!!.jsonPrimitive.int)
        assertEquals("draft", root["stage"]!!.jsonPrimitive.content)
    }

    @Test fun signedManifestRepositoryUrlsMatchAndroidAllowlist() {
        val manifest = listOf(java.io.File("../config/manifest.json"), java.io.File("../../config/manifest.json"))
            .first { it.isFile }
        val root = Json.parseToJsonElement(manifest.readText()).jsonObject
        root["repositories"]!!.jsonArray.map { it.jsonObject }.forEach { repository ->
            val resolvedUrl = repository["source"]!!.jsonObject["resolvedUrl"]!!.jsonPrimitive.content
            assertEquals(true, resolvedUrl.startsWith("https://github.com/"))
        }
    }
}
