/**
 * 文件分析功能扩展脚本
 * 提供文件上传、预览和深度AI分析功能
 * 
 * 不依赖chat.js中的函数，完全独立
 */

let isAnalyzing = false;

/**
 * 深度分析已上传的文件
 */
async function analyzeAttachedFilesAI() {
    // 从全局作用域获取必要的变量
    if (typeof window.attachedFiles === 'undefined' || !window.attachedFiles) {
        alert('请先上传文件');
        return;
    }
    
    if (window.attachedFiles.length === 0) {
        alert('请先上传文件');
        return;
    }
    
    if (isAnalyzing) {
        alert('正在分析中，请稍候...');
        return;
    }
    
    isAnalyzing = true;
    const chatStatus = document.getElementById('chatStatus');
    if (chatStatus) chatStatus.textContent = '🔍 深度分析中...';
    
    try {
        const formData = new FormData();
        
        // 添加所有附加的文件
        for (let fileObj of window.attachedFiles) {
            formData.append('files', fileObj.file);
        }
        
        // 显示分析开始提示
        if (typeof window.addAssistantMessage === 'function') {
            window.addAssistantMessage('📊 正在分析您上传的文件，请稍候...');
        }
        if (typeof window.showTypingIndicator === 'function') {
            window.showTypingIndicator();
        }
        
        const resp = await fetch('/api/analyze-files', {
            method: 'POST',
            body: formData
        });
        
        const data = await resp.json();
        
        if (typeof window.hideTypingIndicator === 'function') {
            window.hideTypingIndicator();
        }
        
        if (resp.ok) {
            // 显示文件分析摘要
            let summary = '📁 **文件分析结果**\n\n';
            
            if (data.files && data.files.length > 0) {
                summary += '**上传文件：**\n';
                data.files.forEach((file, idx) => {
                    summary += `${idx + 1}. ${file.filename} (${file.format} - ${(file.size / 1024).toFixed(1)}KB)\n`;
                });
                summary += '\n';
            }
            
            if (data.errors && data.errors.length > 0) {
                summary += '**处理错误：**\n';
                data.errors.forEach(err => {
                    summary += `- ${err}\n`;
                });
                summary += '\n';
            }
            
            if (data.ai_analysis) {
                summary += '**AI 深度分析：**\n' + data.ai_analysis;
            }
            
            if (typeof window.addAssistantMessage === 'function') {
                window.addAssistantMessage(summary);
            }
            
            // 清空附加文件
            if (window.attachedFiles) {
                window.attachedFiles.length = 0; // 原地清空数组，保持引用一致
            }
            // window.attachedFiles = []; // 避免创建新引用
            
            const filePreview = document.getElementById('filePreview');
            if (filePreview) {
                filePreview.innerHTML = '';
                filePreview.classList.remove('has-files');
            }
            
            if (chatStatus) {
                chatStatus.textContent = '✅ 分析完成';
                setTimeout(() => {
                    chatStatus.textContent = '随时为您解答各种问题';
                }, 2000);
            }
        } else {
            const errorMsg = '❌ 分析失败: ' + (data.error || '未知错误');
            if (typeof window.addAssistantMessage === 'function') {
                window.addAssistantMessage(errorMsg);
            } else {
                alert(errorMsg);
            }
        }
    } catch (err) {
        console.error('Analysis error:', err);
        if (typeof window.hideTypingIndicator === 'function') {
            window.hideTypingIndicator();
        }
        const errMsg = '❌ 分析过程出错: ' + err.message;
        if (typeof window.addAssistantMessage === 'function') {
            window.addAssistantMessage(errMsg);
        } else {
            alert(errMsg);
        }
        if (chatStatus) chatStatus.textContent = '❌ 分析失败';
    } finally {
        isAnalyzing = false;
    }
}

/**
 * 快速分析单个文件
 */
async function quickAnalyzeFile(file) {
    const formData = new FormData();
    formData.append('files', file);
    
    try {
        const resp = await fetch('/api/upload-file', {
            method: 'POST',
            body: formData
        });
        
        const data = await resp.json();
        
        if (data.success_count > 0) {
            return data.files[0];
        } else {
            throw new Error(data.errors ? data.errors[0] : '分析失败');
        }
    } catch (err) {
        console.error('Quick analysis error:', err);
        throw err;
    }
}

/**
 * 显示文件分析详情面板
 */
function showFileAnalysisDetails(fileAnalysis) {
    let details = '📄 **文件详情**\n\n';
    details += `**文件名：** ${fileAnalysis.filename}\n`;
    details += `**类型：** ${fileAnalysis.type}\n`;
    details += `**格式：** ${fileAnalysis.format}\n`;
    details += `**大小：** ${(fileAnalysis.size / 1024).toFixed(1)}KB\n\n`;
    
    if (fileAnalysis.type === 'image') {
        if (fileAnalysis.dimensions) {
            details += `**尺寸：** ${fileAnalysis.dimensions[0]} × ${fileAnalysis.dimensions[1]} px\n`;
        }
        if (fileAnalysis.analysis && fileAnalysis.analysis.colors) {
            details += `**主要颜色：** ${fileAnalysis.analysis.colors.slice(0, 3).map(c => c.hex).join(', ')}\n`;
        }
    } else {
        if (fileAnalysis.analysis) {
            details += `**字符数：** ${fileAnalysis.analysis.char_count || 0}\n`;
            details += `**单词数：** ${fileAnalysis.analysis.word_count || 0}\n`;
            if (fileAnalysis.analysis.line_count) {
                details += `**行数：** ${fileAnalysis.analysis.line_count}\n`;
            }
            if (fileAnalysis.analysis.page_count) {
                details += `**页数：** ${fileAnalysis.analysis.page_count}\n`;
            }
        }
        if (fileAnalysis.text_preview) {
            details += `\n**内容预览：**\n\`\`\`\n${fileAnalysis.text_preview}\n\`\`\``;
        }
    }
    
    if (typeof window.addAssistantMessage === 'function') {
        window.addAssistantMessage(details);
    }
}

// 初始化函数 - 在DOM加载完成后执行
function initFileAnalysis() {
    // 暴露全局接口供HTML调用
    window.fileAnalysis = {
        analyzeFiles: analyzeAttachedFilesAI,
        quickAnalyze: quickAnalyzeFile,
        showDetails: showFileAnalysisDetails
    };
    
    console.log('✅ FileAnalysis module initialized');
}

// 在DOM加载完成或已完成时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFileAnalysis);
} else {
    initFileAnalysis();
}
