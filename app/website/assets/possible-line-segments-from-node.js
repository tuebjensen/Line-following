export function possibleLineSegmentsFromNode(lineSegments, nodeId) {
    return lineSegments.filter(lineSegment =>
        lineSegment.start.id === nodeId ||
        lineSegment.end.id === nodeId
    )
}