package org.wcs.sharc.classifier

import android.content.Context
import android.graphics.Bitmap
import org.tensorflow.lite.Interpreter
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.FileChannel

data class SpeciesPrediction(
    val species: String,
    val confidence: Float,
    val confidencePercentage: String = String.format("%.1f%%", confidence * 100)
)

enum class ConfidenceTier {
    HIGH, MODERATE, UNCERTAIN
}

data class IdentificationResult(
    val topSpecies: String,
    val topConfidence: Float,
    val tier: ConfidenceTier,
    val topCandidates: List<SpeciesPrediction>,
    val recommendedNextAngles: List<String>,
    val diagnosticNotes: String
)

class ElasmobranchMobileClassifier(private val context: Context) {

    private var interpreter: Interpreter? = null
    private val imgSize = 224
    private val mean = floatArrayOf(0.485f, 0.456f, 0.406f)
    private val std = floatArrayOf(0.229f, 0.224f, 0.225f)

    val speciesList = listOf(
        "Bathytoshia lata",
        "Galeocerdo cuvier",
        "Himantura uarnak",
        "Maculabatis ambigua",
        "Mobula kuhlii",
        "Neotrygon caeruleopunctata",
        "Pateobatis fai",
        "Pliotrema annae",
        "Rhinoptera jayakari",
        "Squalus mahia",
        "Taeniurops meyeni"
    )

    init {
        try {
            val modelBuffer = loadModelFile("elasmobranch_mobilenet.tflite")
            val options = Interpreter.Options().apply {
                setNumThreads(4)
                setUseNNAPI(true) // Accelerate on Android NPU
            }
            interpreter = Interpreter(modelBuffer, options)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun loadModelFile(modelName: String): ByteBuffer {
        val assetFileDescriptor = context.assets.openFd(modelName)
        val inputStream = FileInputStream(assetFileDescriptor.fileDescriptor)
        val fileChannel = inputStream.channel
        val startOffset = assetFileDescriptor.startOffset
        val declaredLength = assetFileDescriptor.declaredLength
        return fileChannel.map(FileChannel.MapMode.READ_ONLY, startOffset, declaredLength)
    }

    fun classify(bitmap: Bitmap): IdentificationResult {
        val resized = Bitmap.createScaledBitmap(bitmap, imgSize, imgSize, true)
        val byteBuffer = ByteBuffer.allocateDirect(1 * imgSize * imgSize * 3 * 4).apply {
            order(ByteOrder.nativeOrder())
        }

        val intValues = IntArray(imgSize * imgSize)
        resized.getPixels(intValues, 0, imgSize, 0, 0, imgSize, imgSize)

        var pixel = 0
        for (i in 0 until imgSize) {
            for (j in 0 until imgSize) {
                val p = intValues[pixel++]
                val r = (((p shr 16) and 0xFF) / 255.0f - mean[0]) / std[0]
                val g = (((p shr 8) and 0xFF) / 255.0f - mean[1]) / std[1]
                val b = ((p and 0xFF) / 255.0f - mean[2]) / std[2]
                byteBuffer.putFloat(r)
                byteBuffer.putFloat(g)
                byteBuffer.putFloat(b)
            }
        }

        val outputArray = Array(1) { FloatArray(speciesList.size) }
        interpreter?.run(byteBuffer, outputArray)

        val probs = outputArray[0]
        val sortedIndices = probs.indices.sortedByDescending { probs[it] }

        val top3 = sortedIndices.take(3).map { idx ->
            SpeciesPrediction(speciesList[idx], probs[idx])
        }

        val topConf = top3[0].confidence
        val tier = when {
            topConf >= 0.80f -> ConfidenceTier.HIGH
            topConf >= 0.60f -> ConfidenceTier.MODERATE
            else -> ConfidenceTier.UNCERTAIN
        }

        val nextAngles = if (tier != ConfidenceTier.HIGH) {
            listOf(
                "Ventral view (mouth, gill slits, and disc color)",
                "Tail base and sting (presence/absence of skin folds)",
                "Close-up of head / snout"
            )
        } else emptyList()

        return IdentificationResult(
            topSpecies = top3[0].species,
            topConfidence = topConf,
            tier = tier,
            topCandidates = top3,
            recommendedNextAngles = nextAngles,
            diagnosticNotes = if (tier != ConfidenceTier.HIGH) "Confidence below 80%. Submit additional angles." else "Strong match."
        )
    }
}
