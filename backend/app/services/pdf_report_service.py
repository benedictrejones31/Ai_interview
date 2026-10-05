import os
import logging
from typing import Dict, Any, List
import pymupdf

logger = logging.getLogger(__name__)

class PDFReportService:
    @staticmethod
    def generate_report_pdf(report_data: Dict[str, Any], output_path: str = None) -> bytes:
        """
        Generate a professional multi-page PDF evaluation report from report_data using PyMuPDF.
        """
        doc = pymupdf.open()
        
        # Color palette
        NAVY = (15 / 255, 23 / 255, 42 / 255)
        BRAND_BLUE = (37 / 255, 99 / 255, 235 / 255)
        SKY_BLUE = (56 / 255, 189 / 255, 248 / 255)
        DARK_GRAY = (51 / 255, 65 / 255, 85 / 255)
        LIGHT_BG = (248 / 255, 250 / 255, 252 / 255)
        BORDER_GRAY = (226 / 255, 232 / 255, 240 / 255)
        GREEN = (22 / 255, 163 / 255, 74 / 255)
        AMBER = (217 / 255, 119 / 255, 6 / 255)
        WHITE = (1, 1, 1)

        # Page 1: Executive Summary & Competency Pillars
        page = doc.new_page(width=595, height=842) # A4 size
        
        # 1. Header Banner
        header_rect = pymupdf.Rect(0, 0, 595, 90)
        page.draw_rect(header_rect, color=None, fill=NAVY)
        
        page.insert_text(pymupdf.Point(40, 42), "AI VOICE INTERVIEWER", fontsize=20, fontname="helv", color=WHITE)
        page.insert_text(pymupdf.Point(40, 64), "OFFICIAL CANDIDATE EVALUATION REPORT", fontsize=10, fontname="helv", color=SKY_BLUE)
        page.insert_text(pymupdf.Point(420, 52), "CONFIDENTIAL", fontsize=11, fontname="helv", color=WHITE)

        # 2. Candidate Metadata Card
        meta_rect = pymupdf.Rect(40, 105, 555, 185)
        page.draw_rect(meta_rect, color=BORDER_GRAY, fill=LIGHT_BG, width=1)

        candidate_name = report_data.get("candidate_name", "Candidate")
        interview_date = report_data.get("interview_date", "Recent")
        duration = report_data.get("duration_minutes", 15.0)
        total_q = report_data.get("total_questions_asked", 10)
        overall_score = report_data.get("overall_score", 75)
        recommendation = report_data.get("recommendation", "Human Review Recommended")

        page.insert_text(pymupdf.Point(55, 130), f"Candidate: {candidate_name}", fontsize=14, fontname="helv", color=NAVY)
        page.insert_text(pymupdf.Point(55, 150), f"Interview Date: {interview_date}  |  Duration: {duration} mins", fontsize=10, fontname="helv", color=DARK_GRAY)
        page.insert_text(pymupdf.Point(55, 168), f"Questions Evaluated: {total_q}  |  Assessment: Standard Technical Interview", fontsize=10, fontname="helv", color=DARK_GRAY)

        # Score Badge on right
        score_rect = pymupdf.Rect(425, 115, 540, 175)
        score_color = GREEN if overall_score >= 75 else (BRAND_BLUE if overall_score >= 60 else AMBER)
        page.draw_rect(score_rect, color=score_color, fill=score_color, width=1)
        page.insert_text(pymupdf.Point(445, 142), "OVERALL SCORE", fontsize=8, fontname="helv", color=WHITE)
        page.insert_text(pymupdf.Point(452, 165), f"{overall_score}/100", fontsize=16, fontname="helv", color=WHITE)

        # 3. Recommendation Bar
        rec_rect = pymupdf.Rect(40, 195, 555, 225)
        page.draw_rect(rec_rect, color=BORDER_GRAY, fill=LIGHT_BG, width=1)
        page.insert_text(pymupdf.Point(55, 215), f"Hiring Recommendation: {recommendation}", fontsize=11, fontname="helv", color=NAVY)

        # 4. Competency Pillars
        page.insert_text(pymupdf.Point(40, 250), "EVALUATION BY COMPETENCY PILLAR", fontsize=12, fontname="helv", color=BRAND_BLUE)
        
        cat_scores = report_data.get("category_scores", {})
        pillars = [
            ("Technical Knowledge", cat_scores.get("technical_knowledge", overall_score)),
            ("Project Understanding", cat_scores.get("project_understanding", overall_score)),
            ("Problem Solving", cat_scores.get("problem_solving", overall_score)),
            ("Communication Clarity", cat_scores.get("communication_clarity", overall_score)),
            ("Resume Understanding", cat_scores.get("resume_understanding", overall_score)),
        ]

        y_pos = 270
        for name, score in pillars:
            page.insert_text(pymupdf.Point(55, y_pos + 12), name, fontsize=10, fontname="helv", color=NAVY)
            page.insert_text(pymupdf.Point(230, y_pos + 12), f"{score}/100", fontsize=10, fontname="helv", color=DARK_GRAY)
            # Background bar
            page.draw_rect(pymupdf.Rect(280, y_pos + 2, 540, y_pos + 14), color=BORDER_GRAY, fill=BORDER_GRAY)
            # Active bar
            bar_w = 280 + int((540 - 280) * (score / 100))
            page.draw_rect(pymupdf.Rect(280, y_pos + 2, bar_w, y_pos + 14), color=BRAND_BLUE, fill=BRAND_BLUE)
            y_pos += 26

        # 5. Strengths & Improvements
        y_pos += 15
        page.insert_text(pymupdf.Point(40, y_pos), "KEY STRENGTHS & OBSERVED PROFICIENCIES", fontsize=12, fontname="helv", color=GREEN)
        y_pos += 18
        for st in report_data.get("strengths", [])[:3]:
            page.insert_text(pymupdf.Point(55, y_pos), f"+  {st[:95]}", fontsize=9, fontname="helv", color=DARK_GRAY)
            y_pos += 16

        y_pos += 10
        page.insert_text(pymupdf.Point(40, y_pos), "AREAS FOR TECHNICAL GROWTH", fontsize=12, fontname="helv", color=AMBER)
        y_pos += 18
        for area in report_data.get("areas_for_improvement", [])[:3]:
            page.insert_text(pymupdf.Point(55, y_pos), f"-  {area[:95]}", fontsize=9, fontname="helv", color=DARK_GRAY)
            y_pos += 16

        # 6. Executive Summary Box
        y_pos += 15
        summary_rect = pymupdf.Rect(40, y_pos, 555, y_pos + 70)
        page.draw_rect(summary_rect, color=BORDER_GRAY, fill=LIGHT_BG, width=1)
        page.insert_text(pymupdf.Point(50, y_pos + 18), "Executive Summary:", fontsize=10, fontname="helv", color=NAVY)
        summary_text = report_data.get("final_summary", "")
        # Simple word wrap
        words = summary_text.split()
        line = ""
        line_y = y_pos + 34
        for w in words:
            if len(line + " " + w) > 95:
                page.insert_text(pymupdf.Point(50, line_y), line, fontsize=8.5, fontname="helv", color=DARK_GRAY)
                line = w
                line_y += 13
                if line_y > y_pos + 65:
                    break
            else:
                line += " " + w if line else w
        if line and line_y <= y_pos + 65:
            page.insert_text(pymupdf.Point(50, line_y), line, fontsize=8.5, fontname="helv", color=DARK_GRAY)

        # Footer Page 1
        page.insert_text(pymupdf.Point(40, 815), "AI Voice Interview Platform  |  Confidential Recruiter Report", fontsize=8, fontname="helv", color=DARK_GRAY)
        page.insert_text(pymupdf.Point(520, 815), "Page 1 of 2", fontsize=8, fontname="helv", color=DARK_GRAY)

        # -------------------------------------------------------------
        # Page 2: Question-By-Question Detailed Breakdown
        # -------------------------------------------------------------
        page2 = doc.new_page(width=595, height=842)
        
        # Mini Header
        p2_header = pymupdf.Rect(0, 0, 595, 50)
        page2.draw_rect(p2_header, color=None, fill=NAVY)
        page2.insert_text(pymupdf.Point(40, 32), f"Question-By-Question Breakdown: {candidate_name}", fontsize=14, fontname="helv", color=WHITE)

        q_analyses = report_data.get("question_analyses", [])
        qy = 70
        for i, qa in enumerate(q_analyses[:10], start=1):
            if qy > 740:
                # Add extra page if needed
                page2 = doc.new_page(width=595, height=842)
                qy = 40

            q_title = f"Q{i}. [{qa.get('category', 'technical').upper()}] {qa.get('question', '')}"
            q_score = qa.get("score", 75)
            
            # Card
            q_card = pymupdf.Rect(40, qy, 555, qy + 64)
            page2.draw_rect(q_card, color=BORDER_GRAY, fill=LIGHT_BG, width=1)
            
            page2.insert_text(pymupdf.Point(50, qy + 16), q_title[:90], fontsize=9, fontname="helv", color=NAVY)
            page2.insert_text(pymupdf.Point(490, qy + 16), f"Score: {q_score}/100", fontsize=9, fontname="helv", color=BRAND_BLUE)
            
            answer_text = qa.get("candidate_answer", "")
            page2.insert_text(pymupdf.Point(50, qy + 32), f"Spoken Answer: {answer_text[:100]}...", fontsize=8, fontname="helv", color=DARK_GRAY)
            
            feedback_text = qa.get("feedback", "")
            page2.insert_text(pymupdf.Point(50, qy + 48), f"Feedback: {feedback_text[:100]}", fontsize=8, fontname="helv", color=DARK_GRAY)

            qy += 72

        page2.insert_text(pymupdf.Point(40, 815), "AI Voice Interview Platform  |  Recruiter & HR Assessment", fontsize=8, fontname="helv", color=DARK_GRAY)
        page2.insert_text(pymupdf.Point(520, 815), "Page 2", fontsize=8, fontname="helv", color=DARK_GRAY)

        pdf_bytes = doc.tobytes()
        doc.close()

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
            logger.info(f"Report PDF saved to {output_path}")

        return pdf_bytes
