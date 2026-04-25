# PICOPATT Progress Review - April 24, 2026

I use this as my speaking script for the updated April 24 deck. I stay close to the slide text, but I add enough explanation that I can speak naturally without reading every line.

## Slide 1 - Title
I open with the project name, my name, and the short framing: this is the PICOPATT internship progress review for Phase 2. My key message is that the work is no longer just setup; it is now about explainable clustering for spatio-temporal picoclimatic data, with a path toward paper output.

If I want a slightly fuller opening, I say that the current deck shows where the pipeline stands after the implementation sprint, what is already validated, and what still needs to be decided before the final paper direction is locked.

## Slide 2 - Objectives
I explain that there are two objectives running in parallel. The first is methodological: I keep the explanation in raw sensor units, so the output remains readable as temperature, humidity, wind speed, or similar physical quantities. The second is communicative: I keep the work paper-ready, so the benchmarking and validation story is coherent enough for a manuscript.

When I mention stability, I am precise: the deck now treats stability as cross-seed agreement on the explanation features, not just whether clustering scores are good. That distinction matters because a good silhouette score alone does not guarantee a stable explanation.

## Slide 3 - Internship Arc
I describe the arc in three stages: literature review, implementation sprint, and Phase 2 consolidation. The review draft is done, the implementation path is now running across proxy datasets, and my current task is to turn those pieces into a clean research direction.

I emphasize that the sprint was useful because it turned a whiteboard idea into a working benchmark pipeline. That means the remaining work is less about building from scratch and more about choosing the right framing, freezing the output contract, and deciding which path deserves the paper emphasis.

## Slide 4 - Pipeline Architecture
I walk the audience through the pipeline from left to right. I start with the data layer: either raw sensor time series or engineered shapelet distances. Then I move to representation, where the system either stays in the original space or transforms the data into a more structured feature space. From there, clustering happens with KMeans or ExKMC, and the explanation layer uses SHAP and abductive edits.

The point of this slide is that the repository already has an end-to-end chain. The final presentation layer is not just a cosmetic reporting step; it is the place where the output is translated back into something readable by a domain user. The phrase “format to be frozen” is deliberate, because the explanation schema should not keep changing as more methods are added.

## Slide 5 - Key Results
I lead with the strongest practical result: mixed-length shapelets outperform fixed-length shapelets across the three ablation datasets. The average gain is 17.6 percent in silhouette, which is why the slide highlights silhouette rather than trying to overclaim on every metric.

Then I separate that from the stability result. The 6-seed metric is about explanation stability, specifically top-feature overlap, and it is not the same as clustering quality. If I am asked about the dataset labels, I clarify that ECG200 and ECG5000 refer to the canonical time-series lengths used in those datasets, not sample counts.

For Roma taxi, I note that the result uses engineered temporal features, which is why it is still a useful benchmark even though it is not raw spatial sensor data. The message is that the shapelet-length ablation is strong, but the later raw-vs-shapelet sanity check is dataset-dependent, so I should not oversell shapelets as universally better.

## Slide 6 - Validated vs Still Needed
I use this slide as the boundary of what is actually solid today. The validated side is the complete proxy pipeline, the explanation stack, the 6-seed stability sweep, and the additional baselines that are already runnable. The still-needed side is the real PICOPATT data, a final explanation wording contract, and broader benchmarking before the paper claim is final.

The newer stability refresh matters because it confirms the explanation signal is repeatable across datasets, but it also shows the raw-vs-shapelet comparison is not one-directional. That nuance is useful: it keeps the story credible without weakening the main shapelet-length ablation result.

I explain that this is not a list of failures; it is a project control list. Everything on the validated side is evidence that the current direction is viable. Everything on the still-needed side is what must be resolved before the work can be framed as a final result rather than a development milestone.

## Slide 7 - Core Research Problem
This is the motivation slide. The underlying problem is not only clustering. It is preserving the meaning of the explanation when the representation changes, the window changes, or the feature format changes.

The phrase I want to land is that the system should stay in the same “sensor language.” In other words, if the cluster explanation says something about humidity or temperature, that meaning should not drift just because a different window size or representation was used underneath. That is why I emphasize alignment and stability.

## Slide 8 - Proposed Directions
I explain the two directions as a strategic choice. Direction A is the neural route: autoencoder or latent representation first, then clustering. It is more ambitious and may be more flexible, but the interpretability gap is larger because the explanation has to be mapped back from the latent space.

Direction B is the statistical aggregation route. It keeps the features in direct sensor units and is therefore easier to explain. My hybrid recommendation is practical: use B as the clean baseline and A as the comparator. That gives me a stable reference point and a more experimental neural line if I need it later.

## Slide 9 - Decision Points
I treat this slide as the meeting agenda. The first question is whether to pivot to real PICOPATT data now or after the proxy benchmark is fully closed. My position is cautious: I wait until the proxy story is complete so the methodological comparison stays strong.

The second question is the paper angle. If the work leans toward methods, then the clustering and explanation pipeline is the central contribution. If it leans toward application, then PICOPATT and the urban-planning context take the lead. The third question is format control: I freeze the output schema now, before the method list expands again. The fourth question is whether ExKMC stays the main explainable baseline or whether XClusters becomes the more novel next experiment.

## Slide 10 - Timeline
I walk through the timeline as the remaining execution plan from late April to August. My practical sequence is: validate the proxy work, expand the benchmark set, lock the paper direction, and leave space for revision and submission.

I can give a slightly fuller opening by saying that the current deck shows where the pipeline stands after the implementation sprint, what is already validated, and what still needs to be decided before the final paper direction is locked.

## Slide 11 - Scope Reminder
I am explicit that the real PICOPATT data is still unavailable in this context. The current picoclimate work is a simulated fixture used for validation, so it is useful for pipeline testing but not sufficient for final deployment claims.

This is an important clarification because it prevents over-reading the results. The current evidence supports the method and the workflow. It does not yet support any final claims about the real environment, since that data has not been integrated.

If someone asks about the dataset labels, I clarify that ECG200 and ECG5000 refer to the canonical time-series lengths used in those datasets, not sample counts.

## Slide 12 - What Changed Recently
I use this slide to make the repo audit concrete. The important updates are that the shapelet notebooks were renamed under the \texttt{shapelets\_} prefix, the cross-dataset stability run now uses 6 seeds, HDBSCAN is available in the picoclimate benchmark script, and the autoencoder + KMeans baseline is already runnable.

The newest item here is the raw-vs-shapelet sanity check. I explain that the result is mixed by dataset: shapelets are helpful in some settings, but raw features still compete well in others. That is a more defensible story than saying shapelets always win.

## Slide 13 - Evidence: Stability Across Datasets
This is the main robustness slide. I point to the surrogate CV fidelity band and the top-5 SHAP overlap across 6 seeds.

The line I want to land is that explanation stability is now measured rather than assumed. The 6-seed sweep makes the story auditable, and the feature-overlap signal is strong enough to support the shapelet baseline without pretending the ranking is identical on every dataset.

## Slide 14 - Evidence: Deep Representation Baseline
I use this slide to position the autoencoder as the neural comparator. It is not presented as universally better; it is the deep baseline that tells me whether a more expressive representation actually helps the clustering story.

The quick validation run on the picoclimate fixture is useful because the latent space improved silhouette from 0.154 to 0.229. That gives me a real comparator for the interpretability-gap discussion instead of a hypothetical one.

## Slide 15 - Evidence: Spatial Baseline Expansion
I explain that HDBSCAN widens the benchmark beyond KMeans and ExKMC. The point is to prevent the evaluation from being too narrow and to keep spatial density methods in the PICOPATT story.

I keep the claim modest. The quick benchmark still favors KMeans by silhouette, so HDBSCAN is a broadening baseline rather than the winner. That is still valuable because the goal here is coverage of the benchmark matrix.

## Slide 16 - Interpretation Layer
I start with what is already defensible: the surrogate fidelity is high enough to support explanation, the SHAP output is compact enough to be readable, and stability is now measured instead of assumed.

Then I state the remaining gaps. The explanation template still needs to be frozen in sensor-unit language, the spatial comparators still need real data, and the raw-vs-shapelet sanity check tells me to keep the baseline claims dataset-aware. This slide is the bridge between “it works” and “it is ready to publish.”

## Slide 17 - Recommended Next Phase
I summarize the recommendation as a sequence. First I freeze the output format. Then I keep ExKMC as the baseline. Then I extend the benchmark matrix with spatial methods. Finally, I treat the autoencoder path as the deep comparison line.

I can add that this gives the project a practical two-track structure: a stable sensor-unit baseline and a more ambitious neural comparator. That structure makes it easier to choose later whether the paper leans toward a methods contribution or an application contribution.

## Slide 18 - Reserved Figure Space
I explain that this slide is intentionally left open. It exists as a placeholder for whatever visual evidence is most useful later, such as a cluster profile heatmap, a station map, or a side-by-side comparison of stable and unstable narratives.

The safest way to describe it is as future figure space rather than unfinished content. It gives me room to adapt the deck as the final result set becomes clearer.

## Short delivery version
If I need a concise spoken version, I use this:
- I am now in Phase 2, and the proxy pipeline is already validated end to end.
- I see mixed-length shapelets as a strong ablation result, while the broader raw-vs-shapelet comparison is dataset-dependent.
- My main open decision is whether the paper should be framed as a methods contribution or an application contribution.
- My immediate goal is to freeze the explanation format, broaden the benchmark matrix, and wait for real PICOPATT data before making final claims.
