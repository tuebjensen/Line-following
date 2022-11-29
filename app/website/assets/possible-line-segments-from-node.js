/**
 * @typedef {import('./parse-map').LineSegment} LineSegment
 */

/**
 * Get incident edges (line segments) of the node.
 * @param {LineSegment[]} lineSegments 
 * @param {number} nodeId 
 * @returns {LineSegment[]}
 */
export function getPossibleLineSegmentsFromNode(lineSegments, nodeId) {
    return lineSegments.filter(lineSegment =>
        lineSegment.start.id === nodeId ||
        lineSegment.end.id === nodeId
    )
}