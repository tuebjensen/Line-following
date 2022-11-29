import { possibleLineSegmentsFromNode } from './possible-line-segments-from-node.js'

/**
 * @typedef {import('./parse-map').LineSegment} LineSegment
 * @typedef {import('./parse-map').Point} Point
 * @typedef {import('./parse-map').Node} Node
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
function minDistance(distances, visitedNodeIds) {
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
 * Returns the shortest path tree represented as an array where the value at some index is the id of the parent node.
 * @param {number[][]} graph 
 * @param {number} src 
 * @returns {number[]}
 */
function dijkstra(graph, src) {
    //Array to store the array representation of the SPT (shortest path tree) 
    //Where the index is the id of the node and the element at that index is the preceding node in the SPT 
    const parentArray = []
    //Array to store distances
    const dist = new Array(graph.length) 
    //Array to store vertices in the SPT
    const sptSet = new Array(graph.length)

    for (let i = 0; i < graph.length; i++){
        dist[i] = Infinity
        sptSet[i] = false
    }

    dist[src] = 0
    parentArray[src] = -1
    for (let i = 0; i < graph.length - 1; i++){
        let u = minDistance(dist, sptSet)
        sptSet[u] = true

        for (let v = 0; v < graph.length; v++) {
            if (!sptSet[v] && graph[u][v] != 0 && dist[u] != Infinity && dist[u] + graph[u][v] < dist[v]){
                dist[v] = dist[u] + graph[u][v]
                parentArray[v] = u 
            }
        }
    }
    return parentArray
}
/**
 * Returns whether a line segment is on the path.
 * @param {LineSegment} lineSegment 
 * @param {number} startNodeId 
 * @param {number} endNodeId 
 * @returns {boolean}
 */
function isLineSegmentOnPath(lineSegment, startNodeId, endNodeId){
    return (lineSegment.start.id === startNodeId && lineSegment.end.id === endNodeId || lineSegment.start.id === endNodeId && lineSegment.end.id === startNodeId)
}
/**
 * Returns a base vector in the same direction as the line segment.
 * @param {Node} startNode 
 * @param {Node} endNode 
 * @returns {{x: number, y: number}} 
 */
function directionFromLineSegment(startNode, endNode) {
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
/**
 * Returns the z component of the cross product of the two vectors.
 * @param {{x: number, y: number}} v 
 * @param {{x: number, y: number}} w 
 * @returns {number}
 */
function cross(v, w) {
    return (v.x * w.y) - (v.y * w.x)
}
/**
 * Returns the dot product of the two vectors.
 * @param {{x: number, y: number}} v 
 * @param {{x: number, y: number}} w 
 * @returns {number}
 */
function dot(v, w) {
    return (v.x * w.x) + (v.y * w.y)
}

/**
 * Returns left, right, straight or back depending on which direction the car has to go in order to go from v to w.
 * @param {{x: number, y: number}} v 
 * @param {{x: number, y: number}} w 
 * @returns 
 */
function directionToGo(v, w){
    if ((v.x === 0 && v.y === 0) || (w.x === 0 && w.y === 0)){
        throw new Error('One of the vectors is the zero vector')
    }
    const crossProduct = cross(v, w)
    const dotProduct = dot(v, w) 
    if (dotProduct === 0) {
        if (crossProduct === 1) {
            return 'right'
        } else {
            return 'left'
        }
    } else if (dotProduct > 0){
        return 'straight'
    } else {
        return 'back'
    }
}

/**
 * Returns an object containing the possible directions, the direction of the path and the node id
 * @param {number[]} pathIds 
 * @param {LineSegment[]} lineSegments 
 * @param {Node[]} nodes 
 * @returns 
 */

function generatePathObject(pathIds, lineSegments, nodes) {
    const pathFromSourceToTarget = []
    let orientation = null
    let lastNodeId = null
    for (let i = 0; i < pathIds.length - 1; i++) {
        let possibilities = []
        let choose = ''
        let nodeId = pathIds[i]
        let nextNodeId = pathIds[i + 1]
        let possibleLineSegments = possibleLineSegmentsFromNode(lineSegments, nodeId)   

        if (orientation == null) {
            for (let j = 0; j < possibleLineSegments.length; j++){
                orientation = directionFromLineSegment(nodes[nodeId], nodes[nextNodeId])

                if (isLineSegmentOnPath(possibleLineSegments[j], nodeId, nextNodeId)) {
                }
            }
        } else {
            orientation = directionFromLineSegment(nodes[lastNodeId], nodes[nodeId])
        }

        for (let j = 0; j < possibleLineSegments.length; j++){
            let possibleLineSegment = possibleLineSegments[j]
            let possibleNodeId = nodeId === possibleLineSegment.start.id ? possibleLineSegment.end.id : possibleLineSegment.start.id
            let direction = directionFromLineSegment(nodes[nodeId], nodes[possibleNodeId])
            let instruction = directionToGo(orientation, direction)
            possibilities.push(instruction)
            if (isLineSegmentOnPath(possibleLineSegment, nodeId, nextNodeId)) {
                choose = instruction
            }
            
        }
        lastNodeId = nodeId
        pathFromSourceToTarget.push({possibilities: possibilities, choose: choose, nodeId: nodeId})
    }
    pathFromSourceToTarget.push({possibilities: [], choose: '', nodeId: pathIds[pathIds.length - 1]})
    console.log(pathFromSourceToTarget)
    return pathFromSourceToTarget
}

/**
 * Returns a path from source to target
 * @param {{lineSegments: LineSegment[], nodes: Node[]}} map 
 * @param {number} source 
 * @param {number} target 
 * @returns {{possibilities: string[], choose: string, nodeId: number}}
 */

export function findPath(map, source, target) {
    const lineSegments = map.lineSegments
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