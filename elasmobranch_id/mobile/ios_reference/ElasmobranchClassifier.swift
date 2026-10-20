//
//  ElasmobranchClassifier.swift
//  Standalone On-Device Shark & Ray Identification for iOS (SwiftUI + Vision / CoreML)
//

import Foundation
import UIKit
import CoreML
import Vision

public struct SpeciesPrediction: Identifiable {
    public let id = UUID()
    public let species: String
    public let confidence: Float
    public var confidencePercentage: String {
        return String(format: "%.1f%%", confidence * 100)
    }
}

public enum ConfidenceTier {
    case high
    case moderate
    case uncertain
}

public struct IdentificationResult {
    public let topSpecies: String
    public let topConfidence: Float
    public let tier: ConfidenceTier
    public let topCandidates: [SpeciesPrediction]
    public let recommendedNextAngles: [String]
    public let diagnosticNotes: String
}

public class ElasmobranchMobileClassifier {
    private var vnModel: VNCoreMLModel?

    // Known species list
    public let speciesList: [String] = [
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
    ]

    public init() {
        // Load compiled CoreML model (.mlmodelc) from App Bundle
        // guard let modelURL = Bundle.main.url(forResource: "elasmobranch_mobilenet", withExtension: "mlmodelc"),
        //       let mlModel = try? MLModel(contentsOf: modelURL),
        //       let vnCoreMLModel = try? VNCoreMLModel(for: mlModel) else {
        //     print("CoreML model not found in bundle")
        //     return
        // }
        // self.vnModel = vnCoreMLModel
    }

    /// Run classification on a single UIImage
    public func classify(image: UIImage, completion: @escaping (Result<IdentificationResult, Error>) -> Void) {
        guard let cgImage = image.cgImage else {
            completion(.failure(NSError(domain: "ImageError", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid CGImage"])))
            return
        }

        // Using Vision request
        guard let model = self.vnModel else {
            completion(.failure(NSError(domain: "ModelError", code: -2, userInfo: [NSLocalizedDescriptionKey: "Model not loaded"])))
            return
        }

        let request = VNCoreMLRequest(model: model) { [weak self] (req, error) in
            if let err = error {
                completion(.failure(err))
                return
            }

            guard let results = req.results as? [VNClassificationObservation],
                  let top = results.first else {
                completion(.failure(NSError(domain: "InferenceError", code: -3, userInfo: [NSLocalizedDescriptionKey: "No classification returned"])))
                return
            }

            let top3 = results.prefix(3).map {
                SpeciesPrediction(species: $0.identifier, confidence: $0.confidence)
            }

            let topConf = top.confidence
            let tier: ConfidenceTier
            if topConf >= 0.80 {
                tier = .high
            } else if topConf >= 0.60 {
                tier = .moderate
            } else {
                tier = .uncertain
            }

            // Diagnostic recommendations
            var nextAngles: [String] = []
            var notes = ""
            if tier != .high {
                nextAngles = [
                    "Ventral view (mouth, gill slits, and disc color)",
                    "Tail base and sting (presence/absence of skin folds)",
                    "Close-up of head / snout"
                ]
                notes = "Confidence is below 80%. Please submit additional anatomical angles to verify identification."
            } else {
                notes = "Identification is strongly consistent with morphological features."
            }

            let finalResult = IdentificationResult(
                topSpecies: top.identifier,
                topConfidence: topConf,
                tier: tier,
                topCandidates: Array(top3),
                recommendedNextAngles: nextAngles,
                diagnosticNotes: notes
            )
            completion(.success(finalResult))
        }

        request.imageCropAndScaleOption = .centerCrop
        let handler = VNImageRequestHandler(cgImage: cgImage, orientation: .up, options: [:])
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                try handler.perform([request])
            } catch {
                completion(.failure(error))
            }
        }
    }
}
