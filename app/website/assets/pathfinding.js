import { getPossibleLineSegmentsFromNode } from "./possible-line-segments-from-node.js"

/**
 * @typedef {import('./parse-map').LineSegment} LineSegment
 * @typedef {import('./parse-map').Point} Point
 */

/**
 * Calculates and returns the length of the given line segment.
 * @param {LineSegment} lineSegment 
 * @returns {number}
 */
function lengthOfLineSegment(lineSegment) {
    return Math.sqrt((lineSegment.start.x - lineSegment.end.x)**2 + (lineSegment.start.y - lineSegment.end.y)**2)
}

/**
 * Makes an adjacency matrix based on the given
 * line segments (which will determine the content of the matrix) 
 * and the number of nodes (which will determine the number of rows and number of columns).
 * @param {LineSegment[]} lineSegments
 * @param {number} numberOfNodes 
 * @returns {number[][]}
 */
function makeAdjacencyMatrix(lineSegments, numberOfNodes) {
    const adjacencyMatrix = Array.from(
        { length: numberOfNodes},
        () => Array.from(
            { length: numberOfNodes },
            () => 0
        )
    )

    for (let i = 0; i < lineSegments.length; i++){
        let lineSegment = lineSegments[i]
        let length = lengthOfLineSegment(lineSegment)
        let startNodeId = lineSegment.start.id
        let endNodeId = lineSegment.end.id
        adjacencyMatrix[startNodeId][endNodeId] = length
        adjacencyMatrix[endNodeId][startNodeId] = length
    }
    return adjacencyMatrix
}

/**
 * Returns the ID with the closest node which hasn't been visited.
 * @param {Record<number, number>} distances The index in the array is the corresponding node ID
 * @param {number[]} visitedNodeIds Array of visited node IDs
 * @returns {number}
 */
function getMinDistance(distances, visitedNodeIds) {
    let min = Infinity
    let nodeIdWithMinDistance = -1

    for (let v = 0; v < visitedNodeIds.length; v++){
        if (visitedNodeIds[v] === false && distances[v] <= min){
            min = distances[v]
            nodeIdWithMinDistance = v
        }
    }

    return nodeIdWithMinDistance
}

/**
 * 
 * @param {*} graph 
 * @param {*} src 
 * @returns 
 */
function dijkstra(graph, src) {
    //Array to store the array representation of the SPT (shortest path tree) 
    //Where the index is the id of the node and the element at that index is the preceding node in the SPT 
    const parentArray = []
    //Array to store distances
    const distances = Array.from({ length: graph.length }, () => Infinity)
    //Array to store vertices in the SPT
    const visitedNodeIds = Array.from({ length: graph.length }, () => false)

    distances[src] = 0
    parentArray[src] = -1
    for (let i = 0; i < graph.length - 1; i++){
        let u = getMinDistance(distances, visitedNodeIds)
        visitedNodeIds[u] = true

        for (let v = 0; v < graph.length; v++) {
            if (!visitedNodeIds[v] && graph[u][v] != 0 && distances[u] != Infinity && distances[u] + graph[u][v] < distances[v]){
                distances[v] = distances[u] + graph[u][v]
                parentArray[v] = u 
            }
        }
    }
    return parentArray
}

function isLineSegmentOnPath(lineSegment, startNodeId, endNodeId){
    return (lineSegment.start.id === startNodeId && lineSegment.end.id === endNodeId || lineSegment.start.id === endNodeId && lineSegment.end.id === startNodeId)
}

function getOrientationFromNodes(startNode, endNode) {

    const direction = {x: 0, y: 0}
    if ((endNode.x - startNode.x) < 0) {
        direction.x = -1
        direction.y = 0
    } else if ((endNode.x - startNode.x) > 0) {
        direction.x = 1
        direction.y = 0
    } else if ((endNode.y - startNode.y) < 0) {
        direction.x = 0
        direction.y = -1
    } else if ((endNode.y - startNode.y) > 0){
        direction.x = 0
        direction.y = 1
    }

    return direction

}

function cross(v, w) {
    //returns the z component of the cross product
    return (v.x * w.y) - (v.y * w.x)
}
function dot(v, w) {
    return (v.x * w.x) + (v.y * w.y)
}

function getDirectionToGo(v, w){
    if ((v.x === 0 && v.y === 0) || (w.x === 0 && w.y === 0)){
        throw new Error('vector bad')
    }
    const crossProduct = cross(v, w)
    const dotProduct = dot(v, w) 
    if (dotProduct === 0) {
        if (crossProduct === 1) {
            return "right"
        } else {
            return "left"
        }
    } else if (dotProduct > 0){
        return "straight"
    } else {
        return "back"
    }
}


function generatePathObject(pathIds, lineSegments, nodes) {
    const pathFromSourceToTarget = [{ possibilities: ['straight'], choose: 'straight', nodeId: pathIds[0] }]
    for (let i = 0; i < pathIds.length - 2; i++) {
        const prevNodeId = pathIds[i]
        const nodeId = pathIds[i + 1]
        const nextNodeId = pathIds[i + 2]
        const prevNode = nodes[prevNodeId]
        const node = nodes[nodeId]
        const nextNode = nodes[nodeId]

        const currentOrientation = getOrientationFromNodes(prevNode, node)
        const possibilities = []
        let choose = ''

        for (const possibleLineSegment of getPossibleLineSegmentsFromNode(lineSegments, nodeId)) {
            const possibleNodeId = nodeId === possibleLineSegment.start.id ? possibleLineSegment.end.id : possibleLineSegment.start.id
            const lineSegmentOrientation = getOrientationFromNodes(node, nodes[possibleNodeId])
            const direction = getDirectionToGo(currentOrientation, lineSegmentOrientation)
            possibilities.push(direction)
            if (isLineSegmentOnPath(possibleLineSegment, nodeId, nextNodeId)) {
                choose = direction
            }            
        }
        pathFromSourceToTarget.push({ possibilities: possibilities, choose: choose, nodeId: nodeId })
    }
    pathFromSourceToTarget.push({possibilities: [], choose: '', nodeId: pathIds[pathIds.length - 1]})
    console.log('generated path', pathFromSourceToTarget)
    return pathFromSourceToTarget
}

export function findPath(map, source, target) {
    // strings used for test:
    //r1t2r3(t4|b5)r6(t5|b5(l2|r4))
    //r1t2r3(t4|b5)r6(t5|b5(l2|r4))r3b2l*
    //_r1_t2_r3_(t4_|b5_r2_t2_r8_)r6_(t5_|b*_b2_(l2_|r4_))
    const lineSegments = map.lineSegments
    //const lineSegments = map.lineSegments.filter(lineSegment => !(lineSegment.start.id === 3 && lineSegment.end.id === 6)) //NOT CORRECT JUST FOR TEST
    const nodes = map.nodes
    const adjacencyMatrix = makeAdjacencyMatrix(lineSegments, nodes.length)
    const sptParentArray = dijkstra(adjacencyMatrix, source)
    console.log(sptParentArray)

    
    const pathIds = [target]
    let foundPath = false
    let newTarget = target
    while (!foundPath) {
        newTarget = sptParentArray[newTarget]
        if (newTarget === -1) {
            foundPath = true
        } else if (sptParentArray[newTarget] == newTarget){
            throw new Error('Target is not present in map')
        } else {
            pathIds.push(newTarget)
        }
    }

    pathIds.reverse()
    console.log(pathIds)
    return generatePathObject(pathIds, lineSegments, nodes)

}