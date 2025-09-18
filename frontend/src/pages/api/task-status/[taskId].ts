import { NextApiRequest, NextApiResponse } from 'next'
import { spawn } from 'child_process'
import path from 'path'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { taskId } = req.query

  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  if (!taskId || typeof taskId !== 'string') {
    return res.status(400).json({ message: 'Task ID is required' })
  }

  try {
          const pythonPath = path.join(process.cwd(), '..', 'venv', 'bin', 'python')
          const scriptPath = path.join(process.cwd(), '..', 'backend', 'check_task_status.py')

    const pythonProcess = spawn(pythonPath, [scriptPath, taskId], {
      cwd: path.join(process.cwd(), '..'),
      env: {
        ...process.env,
      },
    })

    let output = ''
    let errorOutput = ''

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString()
    })

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString()
    })

    const result = await new Promise<any>((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          try {
            resolve(JSON.parse(output))
          } catch (parseError) {
            reject(new Error(`Failed to parse status output: ${output}`))
          }
        } else {
          reject(new Error(`Status check process exited with code ${code}: ${errorOutput}`))
        }
      })
    })

    res.status(200).json(result)

  } catch (error: any) {
    console.error(`Failed to get status for task ${taskId}:`, error)
    res.status(500).json({ success: false, message: error.message })
  }
}
